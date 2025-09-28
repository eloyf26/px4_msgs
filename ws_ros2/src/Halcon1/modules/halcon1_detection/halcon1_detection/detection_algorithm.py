from halcon1_types import DetectionResult
from ultralytics import YOLO
import cv2
import numpy as np
import os
from pathlib import Path

class DetectionAlgorithm:
    def __init__(self):
        self.camera_width = 640
        self.camera_height = 480

        # Models must be installed via colcon build
        # They will be in the package directory after installation
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

        # Model selection priority - use the best available model
        model_preferences = [
            #'yolo11n_fast_accurate.pt',   # Optimized training version
            'yolo11n.pt'                  # Base model fallback
        ]

        # Find the best available model
        self.model_path = None
        self.model_name = None

        for model_name in model_preferences:
            potential_path = self.models_dir / model_name
            if potential_path.exists():
                self.model_path = potential_path
                self.model_name = model_name
                print(f"Using model: {model_name} from {self.models_dir}")
                break

        # If no model found, use base model (will download if needed)
        if self.model_path is None:
            self.model_name = 'yolo11n.pt'
            self.model_path = self.models_dir / self.model_name
            print(f"No trained model found. Will download base model: {self.model_name}")

        # Load the YOLO model
        if self.model_path.exists():
            print(f"Loading model from: {self.model_path}")
            self.model = YOLO(str(self.model_path))
        else:
            print(f"Downloading {self.model_name}...")
            self.model = YOLO(self.model_name)
            # Save to models directory for future use
            if Path(self.model_name).exists():
                import shutil
                shutil.move(self.model_name, str(self.model_path))
                print(f"Model saved to: {self.model_path}")

        # Detection parameters
        self.confidence_threshold = 0.25
        self.nms_threshold = 0.45

        # For drone-specific models, only detect drones (class 0)
        # For base model, detect all objects
        if 'drone' in self.model_name:
            self.target_classes = [0]  # Drone class only
        else:
            self.target_classes = None  # All classes

        print(f"Detection algorithm initialized with {self.model_name}")

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
            best_idx = 0
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

                # Class name
                if 'drone' in self.model_name:
                    class_name = 'drone'
                else:
                    class_name = self.model.names[class_id]

                # Color coding
                if i == best_idx:
                    color = (0, 255, 0)  # Green for primary detection
                    thickness = 3
                else:
                    color = (255, 255, 0)  # Cyan for secondary
                    thickness = 2

                # Draw bounding box
                cv2.rectangle(annotated_image,
                            (int(x1), int(y1)),
                            (int(x2), int(y2)),
                            color, thickness)

                # Draw label
                label = f'{class_name}: {conf:.2f}'
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)

                # Label background
                cv2.rectangle(annotated_image,
                            (int(x1), int(y1) - label_size[1] - 4),
                            (int(x1) + label_size[0], int(y1)),
                            color, -1)

                # Label text
                cv2.putText(annotated_image, label,
                          (int(x1), int(y1) - 2),
                          cv2.FONT_HERSHEY_SIMPLEX,
                          0.5, (0, 0, 0), 2)

            # Use best detection for result
            if best_conf > 0:
                best_box = boxes[best_idx]
                x1, y1, x2, y2 = best_box.xyxy[0].tolist()

                detection_result = DetectionResult(
                    x=int(x1),
                    y=int(y1),
                    width=int(x2 - x1),
                    height=int(y2 - y1)
                )

        # Add info overlay
        model_info = self.model_name.replace('.pt', '')
        num_detections = len(results[0].boxes) if results[0].boxes is not None else 0
        info_text = f"Model: {model_info} | Detections: {num_detections}"

        cv2.putText(annotated_image, info_text,
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                   0.7, (0, 255, 255), 2)

        return detection_result, annotated_image