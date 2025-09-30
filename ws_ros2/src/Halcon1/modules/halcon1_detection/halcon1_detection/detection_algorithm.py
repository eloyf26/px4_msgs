from halcon1_types import DetectionResult
from ultralytics import YOLO
import cv2
import numpy as np
import yaml
from pathlib import Path


class DetectionAlgorithm:
    def __init__(self):
        # Load configuration from YAML file
        self._load_config()

        # Get models directory from package
        try:
            import halcon1_detection
            package_dir = Path(halcon1_detection.__file__).parent
            self.models_dir = package_dir / 'models'
        except ImportError:
            # Fallback if package not properly installed
            print("WARNING: halcon1_detection package not found. Make sure to run 'colcon build'")
            self.models_dir = Path(__file__).parent / 'models'

        # Ensure models directory exists
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Select and load model based on configuration
        self._load_model()

        print(f"Detection algorithm initialized with {self.model_config['name']}")

    def _load_config(self):
        """Load configuration from YAML file."""
        try:
            import halcon1_detection
            package_dir = Path(halcon1_detection.__file__).parent
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

        # Load the YOLO model
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

    def detect(self, image: np.ndarray) -> tuple[DetectionResult, np.ndarray]:
        """
        Detect objects in the image using YOLOv11n.

        Args:
            image: Input image as numpy array (OpenCV format, BGR)

        Returns:
            Tuple of (DetectionResult, annotated_image)
        """
        # Run YOLO detection
        results = self.model(image, conf=self.confidence_threshold, verbose=False)

        # Create annotated image copy
        annotated_image = image.copy()

        # Default result (no detection)
        detection_result = DetectionResult(0, 0, 0, 0)

        if len(results[0].boxes) > 0:
            boxes = results[0].boxes

            # Find best detection (highest confidence)
            best_idx = -1
            best_conf = 0

            for i, box in enumerate(boxes):
                conf = box.conf[0].item()

                # Filter by target classes if specified
                if self.target_classes is not None:
                    class_id = int(box.cls[0].item())
                    if class_id not in self.target_classes:
                        continue

                if conf > best_conf:
                    best_conf = conf
                    best_idx = i

            # Draw all detections
            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                conf = box.conf[0].item()
                class_id = int(box.cls[0].item())

                # Skip if filtering classes and not in target
                if self.target_classes is not None:
                    if class_id not in self.target_classes:
                        continue

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

        # Add info overlay
        viz = self.config['visualization']
        model_info = self.model_config['name'].replace('.pt', '')
        num_detections = len([box for box in results[0].boxes
                             if self.target_classes is None or
                             int(box.cls[0].item()) in self.target_classes]) if results[0].boxes is not None else 0
        info_text = f"Model: {model_info} | Detections: {num_detections}"

        cv2.putText(annotated_image, info_text,
                   (10, 30),
                   viz['font']['type'],
                   viz['font']['info_scale'],
                   tuple(viz['colors']['info']),
                   viz['thickness']['text'])

        return detection_result, annotated_image