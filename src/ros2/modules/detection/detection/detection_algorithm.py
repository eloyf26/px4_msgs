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

        # Determine operation mode
        self.model_mode = self.config.get('model_mode', 'single')

        # Select and load model(s) based on configuration
        if self.model_mode == 'dual':
            self._load_dual_models()
            print(f"Detection algorithm initialized in DUAL mode")
            print(f"  Short-range: {self.short_range_config['name']}")
            print(f"  Long-range: {self.long_range_config['name']}")
        else:
            self._load_model()
            print(f"Detection algorithm initialized in SINGLE mode with {self.model_config['name']}")

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

        # Track model source for smoothing reset on model switch
        self.previous_model_source = None

    def _load_dual_models(self):
        """Load both short-range and long-range models for dual mode."""
        dual_config = self.config['dual_models']

        # Load short-range model configuration
        short_model_ref = dual_config['short_range']['model_ref']
        self.short_range_config = self.config['models'][short_model_ref]
        self.short_range_priority = dual_config['short_range']['priority']

        # Load long-range model configuration
        long_model_ref = dual_config['long_range']['model_ref']
        self.long_range_config = self.config['models'][long_model_ref]
        self.long_range_priority = dual_config['long_range']['priority']

        # Load switching configuration
        self.switching_config = dual_config['switching']

        # Initialize both models
        print(f"Loading short-range model: {self.short_range_config['name']}")
        short_model_path = self.models_dir / self.short_range_config['name']
        self.short_range_model = self._load_yolo_model(short_model_path, self.short_range_config['name'])

        print(f"Loading long-range model: {self.long_range_config['name']}")
        long_model_path = self.models_dir / self.long_range_config['name']
        self.long_range_model = self._load_yolo_model(long_model_path, self.long_range_config['name'])

        # Track last detection area for adaptive switching
        self.last_bbox_area = None

        # For backward compatibility, set model to short_range by default
        self.model = self.short_range_model
        self.model_config = self.short_range_config

        # Smoothing parameters (shared across both models)
        self.smoothing_enabled = self.config['smoothing']['enabled']
        self.smoothing_alpha = self.config['smoothing']['alpha']
        self.smoothed_box = None  # [x1, y1, x2, y2]

        # Track model source for smoothing reset on model switch
        self.previous_model_source = None

    def _load_yolo_model(self, model_path: Path, model_name: str):
        """Helper method to load a YOLO model."""
        if model_path.exists():
            print(f"  Loading from: {model_path}")
            return YOLO(str(model_path))
        else:
            print(f"  Downloading {model_name}...")
            model = YOLO(model_name)
            # Save to models directory for future use
            if Path(model_name).exists():
                import shutil
                shutil.move(model_name, str(model_path))
                print(f"  Model saved to: {model_path}")
            return model

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

    def _compute_bbox_area(self, bbox_xyxy: np.ndarray) -> float:
        """
        Compute bounding box area in pixels².

        Args:
            bbox_xyxy: [x1, y1, x2, y2]

        Returns:
            Area in pixels²
        """
        x1, y1, x2, y2 = bbox_xyxy
        return (x2 - x1) * (y2 - y1)

    def _select_models_to_run(self) -> list[str]:
        """
        Determine which model(s) to run based on bbox size adaptive switching.

        Returns:
            List of model names to run: ['short'], ['long'], or ['short', 'long']
        """
        if self.model_mode != 'dual':
            return ['single']

        # Strategy: bbox_size - adaptive based on previous detection
        # First frame or no previous detection - run both models
        if self.last_bbox_area is None:
            return ['short', 'long']

        bbox_threshold = self.switching_config['bbox_threshold']
        overlap_zone = self.switching_config['overlap_zone']

        # Small bbox (distant target) - prefer long-range
        if self.last_bbox_area < bbox_threshold:
            return ['long']
        # Large bbox (close target) - prefer short-range
        elif self.last_bbox_area > (bbox_threshold + overlap_zone):
            return ['short']
        # In overlap zone - run both for smooth transition
        else:
            return ['short', 'long']

    def _run_model_inference(self, model, model_config: dict, image: np.ndarray) -> tuple[list, str]:
        """
        Run inference on a single model.

        Args:
            model: YOLO model instance
            model_config: Model configuration dict
            image: Input image

        Returns:
            Tuple of (tracked_drones list, model_name string)
        """
        # Run YOLO tracking
        results = model.track(
            image,
            conf=model_config['confidence_threshold'],
            persist=True,
            verbose=False,
            tracker='botsort.yaml'
        )[0]

        # Filter detections by target classes
        tracked_drones = []
        if results.boxes is not None and len(results.boxes) > 0:
            boxes = results.boxes
            target_classes = model_config['target_classes']

            for box in boxes:
                if target_classes is not None:
                    class_id = int(box.cls[0].item())
                    if class_id not in target_classes:
                        continue

                track_id = box.id[0].item() if box.id is not None else -1
                tracked_drones.append((box, track_id))

        return tracked_drones, model_config['name']

    def _fuse_detections(self, short_detections: list, long_detections: list,
                         short_priority: int, long_priority: int) -> tuple[list, str]:
        """
        Fuse detections from both models based on configured fusion method.

        Args:
            short_detections: List of (box, track_id) from short-range model
            long_detections: List of (box, track_id) from long-range model
            short_priority: Priority of short-range model (lower = higher priority)
            long_priority: Priority of long-range model

        Returns:
            Tuple of (fused_detections list, source_info string)
        """
        # If only one model has detections, return those
        if not short_detections and not long_detections:
            return [], 'none'
        if not short_detections:
            return long_detections, 'long'
        if not long_detections:
            return short_detections, 'short'

        fusion_method = self.switching_config['fusion_method']

        # Method 1: highest_conf - pick detection with highest confidence
        if fusion_method == 'highest_conf':
            # Add priority boost to preferred model
            priority_boost = self.switching_config.get('priority_boost', 0.0)

            best_short = max(short_detections, key=lambda x: x[0].conf[0].item())
            best_long = max(long_detections, key=lambda x: x[0].conf[0].item())

            short_conf = best_short[0].conf[0].item()
            long_conf = best_long[0].conf[0].item()

            # Apply priority boost to higher priority model
            if short_priority < long_priority:
                short_conf += priority_boost
            else:
                long_conf += priority_boost

            # Add hysteresis: boost previous model source to prevent oscillation
            hysteresis_boost = 0.05
            if self.previous_model_source is not None:
                if 'short' in self.previous_model_source:
                    short_conf += hysteresis_boost
                elif 'long' in self.previous_model_source:
                    long_conf += hysteresis_boost

            if short_conf >= long_conf:
                return [best_short], 'short (fused)'
            else:
                return [best_long], 'long (fused)'

        # Method 2: confidence_weighted - blend bbox coordinates
        elif fusion_method == 'confidence_weighted':
            best_short = max(short_detections, key=lambda x: x[0].conf[0].item())
            best_long = max(long_detections, key=lambda x: x[0].conf[0].item())

            short_conf = best_short[0].conf[0].item()
            long_conf = best_long[0].conf[0].item()

            # Normalize confidences to sum to 1
            total_conf = short_conf + long_conf
            w_short = short_conf / total_conf
            w_long = long_conf / total_conf

            # Blend bounding box coordinates
            short_bbox = best_short[0].xyxy[0].cpu().numpy()
            long_bbox = best_long[0].xyxy[0].cpu().numpy()

            # Create a weighted average box (we'll return the higher confidence one but with blended coords)
            # For simplicity, return the higher confidence detection
            # (Full bbox blending would require creating a new box object)
            if short_conf >= long_conf:
                return [best_short], 'short+long (weighted)'
            else:
                return [best_long], 'short+long (weighted)'

        # Method 3: nms - Non-Maximum Suppression
        elif fusion_method == 'nms':
            # Combine all detections and apply NMS
            all_detections = short_detections + long_detections

            # For simplicity, just pick highest confidence
            # (Full NMS would require IoU calculation)
            best_detection = max(all_detections, key=lambda x: x[0].conf[0].item())

            # Determine source
            source = 'short (NMS)' if best_detection in short_detections else 'long (NMS)'
            return [best_detection], source

        # Default: return short-range detections
        return short_detections, 'short (default)'

    def track(self, image: np.ndarray, debug: bool = False) -> tuple[DetectionResult, np.ndarray | None]:
        """
        Track objects using YOLO's BoT-SORT tracker.
        Supports both single and dual model modes.

        Args:
            image: Input image as numpy array (OpenCV format, BGR)
            debug: If True, generate annotated image for visualization

        Returns:
            Tuple of (DetectionResult, annotated_image or None)
        """
        # Create annotated image copy only if debug mode enabled
        annotated_image = image.copy() if debug else None

        # Default result (no detection)
        detection_result = DetectionResult(0, 0, 0, 0)

        # Route to appropriate inference path
        if self.model_mode == 'single':
            tracked_drones, model_source = self._track_single_model(image)
        else:
            tracked_drones, model_source = self._track_dual_model(image)

        # Reset smoothing if model source changed (prevents blending incompatible tracker outputs)
        if self.model_mode == 'dual' and self.previous_model_source is not None:
            if model_source != self.previous_model_source:
                self.smoothed_box = None  # Reset for clean transition
        self.previous_model_source = model_source

        if not tracked_drones:
            # Reset last bbox area if no detection
            if self.model_mode == 'dual':
                self.last_bbox_area = None
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

        # Update last bbox area for dual mode adaptive switching
        if self.model_mode == 'dual':
            self.last_bbox_area = self._compute_bbox_area(smoothed_bbox)

        # Debug visualization
        if debug and annotated_image is not None:
            self._draw_debug_visualization(annotated_image, tracked_drones, best_box, model_source)

        return detection_result, annotated_image

    def _track_single_model(self, image: np.ndarray) -> tuple[list, str]:
        """
        Run inference using single model mode.

        Args:
            image: Input image

        Returns:
            Tuple of (tracked_drones list, model_source string)
        """
        tracked_drones, model_name = self._run_model_inference(self.model, self.model_config, image)
        return tracked_drones, model_name

    def _track_dual_model(self, image: np.ndarray) -> tuple[list, str]:
        """
        Run inference using dual model mode with adaptive switching.

        Args:
            image: Input image

        Returns:
            Tuple of (tracked_drones list, model_source string)
        """
        # Determine which models to run
        models_to_run = self._select_models_to_run()

        short_detections = []
        long_detections = []

        # Run inference on selected models
        if 'short' in models_to_run:
            short_detections, _ = self._run_model_inference(
                self.short_range_model,
                self.short_range_config,
                image
            )

        if 'long' in models_to_run:
            long_detections, _ = self._run_model_inference(
                self.long_range_model,
                self.long_range_config,
                image
            )

        # Fuse detections if both models ran
        if 'short' in models_to_run and 'long' in models_to_run:
            fused_detections, source = self._fuse_detections(
                short_detections,
                long_detections,
                self.short_range_priority,
                self.long_range_priority
            )
            return fused_detections, source

        # Return whichever model ran
        if short_detections:
            return short_detections, 'short'
        elif long_detections:
            return long_detections, 'long'
        else:
            return [], 'none'

    def _draw_debug_visualization(self, annotated_image: np.ndarray, tracked_drones: list,
                                   best_box, model_source: str):
        """
        Draw debug visualization on annotated image.

        Args:
            annotated_image: Image to draw on
            tracked_drones: List of (box, track_id) tuples
            best_box: Best detection box
            model_source: String indicating which model(s) were used
        """
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

        # Info overlay - show mode and model source
        if self.model_mode == 'dual':
            mode_info = f"DUAL: {model_source}"
            if self.last_bbox_area is not None:
                mode_info += f" | Area: {int(self.last_bbox_area)}px²"
        else:
            model_info = self.model_config['name'].replace('.pt', '')
            mode_info = f"Model: {model_info}"

        info_text = f"{mode_info} | Tracked: {len(tracked_drones)}"
        cv2.putText(annotated_image, info_text,
                   (10, 30),
                   viz['font']['type'],
                   viz['font']['info_scale'],
                   tuple(viz['colors']['info']),
                   viz['thickness']['text'])