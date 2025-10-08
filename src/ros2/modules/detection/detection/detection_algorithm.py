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

        # Tracking parameters
        self.max_distance_threshold = self.config['tracking']['max_distance_threshold']

        # Tracking state for consistent target selection
        self.last_detection_box = None

    @staticmethod
    def _box_center_distance(box1, box2) -> float:
        """Calculate Euclidean distance between centers of two bounding boxes."""
        x1_1, y1_1, x2_1, y2_1 = box1.xyxy[0].tolist()
        x1_2, y1_2, x2_2, y2_2 = box2.xyxy[0].tolist()

        center1_x = (x1_1 + x2_1) / 2
        center1_y = (y1_1 + y2_1) / 2
        center2_x = (x1_2 + x2_2) / 2
        center2_y = (y1_2 + y2_2) / 2

        return np.sqrt((center1_x - center2_x)**2 + (center1_y - center2_y)**2)

    def detect(self, image: np.ndarray, debug: bool = False) -> tuple[DetectionResult, np.ndarray | None]:
        """
        Detect objects in the image using YOLOv11n.

        Args:
            image: Input image as numpy array (OpenCV format, BGR)
            debug: If True, generate annotated image for visualization

        Returns:
            Tuple of (DetectionResult, annotated_image or None)
        """
        # Run YOLO detection
        results = self.model(image, conf=self.confidence_threshold, verbose=False)

        # Create annotated image copy only if debug mode enabled
        annotated_image = image.copy() if debug else None

        # Default result (no detection)
        detection_result = DetectionResult(0, 0, 0, 0)

        if len(results[0].boxes) <= 0:
            return detection_result, annotated_image

        boxes = results[0].boxes

        # Filter boxes by target classes (e.g., drones only)
        drone_boxes = []
        for i, box in enumerate(boxes):
            if self.target_classes is not None:
                class_id = int(box.cls[0].item())
                if class_id not in self.target_classes:
                    continue
            drone_boxes.append((i, box))

        # Select best detection: prefer closest to previous detection for tracking consistency
        best_idx = -1

        if self.last_detection_box is not None and drone_boxes:
            # Prefer drone closest to last detection (temporal consistency)
            min_distance = float('inf')
            closest_idx = -1
            for i, box in drone_boxes:
                distance = self._box_center_distance(box, self.last_detection_box)
                if distance < min_distance:
                    min_distance = distance
                    closest_idx = i

            # Only use closest if within threshold, otherwise reset to highest confidence
            if min_distance <= self.max_distance_threshold:
                best_idx = closest_idx
            else:
                # Target moved too far or is a different drone - reset tracking
                self.last_detection_box = None
                best_conf = 0
                for i, box in drone_boxes:
                    conf = box.conf[0].item()
                    if conf > best_conf:
                        best_conf = conf
                        best_idx = i
        elif drone_boxes:
            # No previous detection: use highest confidence
            best_conf = 0
            for i, box in drone_boxes:
                conf = box.conf[0].item()
                if conf > best_conf:
                    best_conf = conf
                    best_idx = i

        # Draw all detections (only in debug mode)
        if debug and annotated_image is not None:
            for i, box in drone_boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = box.conf[0].item()
                class_id = int(box.cls[0].item())

                # Get class name
                if self.target_classes == [0]:  # Drone-specific model
                    class_name = 'drone'
                else:
                    class_name = self.model.names[class_id]

                # Get visualization settings
                viz = self.config['visualization']

                # Color and thickness based on whether it's primary detection
                if i == best_idx:
                    color = tuple(viz['colors']['primary'])
                    thickness = viz['thickness']['primary']
                else:
                    color = tuple(viz['colors']['secondary'])
                    thickness = viz['thickness']['secondary']

                # Draw bounding box
                cv2.rectangle(annotated_image,
                            (int(x1), int(y1)),
                            (int(x2), int(y2)),
                            color, thickness)

                # Draw label
                label = f'{class_name}: {conf:.2f}'
                font_type = viz['font']['type']
                font_scale = viz['font']['scale']
                text_thickness = viz['thickness']['text']

                label_size, _ = cv2.getTextSize(label, font_type, font_scale, text_thickness)

                # Label background
                cv2.rectangle(annotated_image,
                            (int(x1), int(y1) - label_size[1] - 4),
                            (int(x1) + label_size[0], int(y1)),
                            color, -1)

                # Label text
                cv2.putText(annotated_image, label,
                        (int(x1), int(y1) - 2),
                        font_type,
                        font_scale,
                        tuple(viz['colors']['text']),
                        text_thickness)

        # Use best detection for result
        if best_idx >= 0:
            best_box = boxes[best_idx]
            x1, y1, x2, y2 = best_box.xyxy[0].tolist()

            detection_result = DetectionResult(
                x=int(x1),
                y=int(y1),
                width=int(x2 - x1),
                height=int(y2 - y1)
            )

            # Store for next frame's tracking consistency
            self.last_detection_box = best_box
        else:
            # No valid detection - clear tracking state
            self.last_detection_box = None

        # Add info overlay (only in debug mode)
        if debug and annotated_image is not None:
            viz = self.config['visualization']
            model_info = self.model_config['name'].replace('.pt', '')
            num_detections = len(drone_boxes)
            info_text = f"Model: {model_info} | Detections: {num_detections}"

            cv2.putText(annotated_image, info_text,
                       (10, 30),
                       viz['font']['type'],
                       viz['font']['info_scale'],
                       tuple(viz['colors']['info']),
                       viz['thickness']['text'])

        return detection_result, annotated_image