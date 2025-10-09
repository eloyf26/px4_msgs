from common_types import DetectionResult
from ultralytics import YOLO
import cv2
import numpy as np
import yaml
from pathlib import Path

# Import extensions to auto-register custom architectures (LMWP-YOLO, etc.)
from . import extensions


class DetectionAlgorithm:
    def __init__(self):
        # Load configuration from YAML file
        self._load_config()

        # Get models directory from package
        try:
            import detection
            package_dir = Path(detection.__file__).parent
            self.models_dir = package_dir / 'models'
        except ImportError:
            # Fallback if package not properly installed
            print("WARNING: detection package not found. Make sure to run 'colcon build'")
            self.models_dir = Path(__file__).parent / 'models'

        # Ensure models directory exists
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Select and load model based on configuration
        self._load_model()

        print(f"Detection algorithm initialized with {self.model_config['name']}")

    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            import detection
            package_dir = Path(detection.__file__).parent
            config_path = package_dir / 'config.yaml'
        except ImportError:
            # Fallback if package not properly installed
            config_path = Path(__file__).parent / 'config.yaml'

        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

    def _load_model(self):
        """Load the configured model."""
        # Get the selected model configuration
        selected_model = self.config['selected_model']
        self.model_config = self.config['models'][selected_model]
        self.model_path = self.models_dir / self.model_config['name']

        print(f"Configured to use model: {self.model_config['name']}")

        # Load the YOLO model (extensions auto-registered, so just use YOLO directly)
        if self.model_path.exists():
            print(f"Loading model from: {self.model_path}")
            self.model = YOLO(str(self.model_path))
        else:
            print(f"Downloading {self.model_config['name']}...")
            self.model = YOLO(self.model_config['name'])
            # Save to models directory for future use
            if Path(self.model_config['name']).exists():
                import shutil
                shutil.move(self.model_config['name'], str(self.model_path))
                print(f"Model saved to: {self.model_path}")

        # Set detection parameters from config
        self.confidence_threshold = self.model_config['confidence_threshold']
        self.nms_threshold = self.model_config['nms_threshold']
        self.target_classes = self.model_config['target_classes']

        # Smoothing parameters
        self.smoothing_enabled = self.config['smoothing']['enabled']
        self.smoothing_alpha = self.config['smoothing']['alpha']
        self.smoothed_box = None  # [x1, y1, x2, y2]

    def _smooth_bbox(self, bbox_xyxy: np.ndarray) -> np.ndarray:
        """
        Apply exponential moving average to bounding box coordinates.

        Args:
            bbox_xyxy: [x1, y1, x2, y2]

        Returns:
            Smoothed [x1, y1, x2, y2]
        """
        if not self.smoothing_enabled:
            return bbox_xyxy

        if self.smoothed_box is None:
            self.smoothed_box = bbox_xyxy
            return bbox_xyxy

        # EMA: smoothed = alpha * new + (1 - alpha) * old
        self.smoothed_box = (self.smoothing_alpha * bbox_xyxy +
                            (1 - self.smoothing_alpha) * self.smoothed_box)

        return self.smoothed_box

    def track(self, image: np.ndarray, debug: bool = False) -> tuple[DetectionResult, np.ndarray | None]:
        """
        Track objects using YOLO's BoT-SORT tracker.

        Args:
            image: Input image as numpy array (OpenCV format, BGR)
            debug: If True, generate annotated image for visualization

        Returns:
            Tuple of (DetectionResult, annotated_image or None)
        """
        # Run YOLO tracking (uses BoT-SORT by default)
        results = self.model.track(
            image,
            conf=self.confidence_threshold,
            persist=True,  # Persist tracker state between frames
            verbose=False,
            tracker='botsort.yaml'  # Explicit tracker config
        )[0]

        # Create annotated image copy only if debug mode enabled
        annotated_image = image.copy() if debug else None

        # Default result (no detection)
        detection_result = DetectionResult(0, 0, 0, 0)

        if results.boxes is None or len(results.boxes) == 0:
            return detection_result, annotated_image

        boxes = results.boxes

        # Filter by target classes
        tracked_drones = []
        for box in boxes:
            if self.target_classes is not None:
                class_id = int(box.cls[0].item())
                if class_id not in self.target_classes:
                    continue

            # BoT-SORT provides tracking IDs
            track_id = box.id[0].item() if box.id is not None else -1
            tracked_drones.append((box, track_id))

        if not tracked_drones:
            return detection_result, annotated_image

        # Select primary target: highest confidence drone
        best_box = max(tracked_drones, key=lambda x: x[0].conf[0].item())[0]

        # Extract and smooth bounding box
        x1, y1, x2, y2 = best_box.xyxy[0].cpu().numpy()
        smoothed_bbox = self._smooth_bbox(np.array([x1, y1, x2, y2]))
        x1, y1, x2, y2 = smoothed_bbox

        detection_result = DetectionResult(
            x=int(x1),
            y=int(y1),
            width=int(x2 - x1),
            height=int(y2 - y1)
        )

        # Debug visualization
        if debug and annotated_image is not None:
            viz = self.config['visualization']

            for box, track_id in tracked_drones:
                bx1, by1, bx2, by2 = box.xyxy[0].tolist()
                conf = box.conf[0].item()

                is_primary = (box == best_box)
                color = tuple(viz['colors']['primary' if is_primary else 'secondary'])
                thickness = viz['thickness']['primary' if is_primary else 'secondary']

                # Draw box
                cv2.rectangle(annotated_image,
                            (int(bx1), int(by1)),
                            (int(bx2), int(by2)),
                            color, thickness)

                # Label with track ID
                label = f'ID:{int(track_id)} {conf:.2f}' if track_id >= 0 else f'drone {conf:.2f}'
                cv2.putText(annotated_image, label,
                           (int(bx1), int(by1) - 5),
                           viz['font']['type'],
                           viz['font']['scale'],
                           color,
                           viz['thickness']['text'])

            # Info overlay
            model_info = self.model_config['name'].replace('.pt', '')
            info_text = f"Model: {model_info} | Tracked: {len(tracked_drones)}"
            cv2.putText(annotated_image, info_text,
                       (10, 30),
                       viz['font']['type'],
                       viz['font']['info_scale'],
                       tuple(viz['colors']['info']),
                       viz['thickness']['text'])

        return detection_result, annotated_image