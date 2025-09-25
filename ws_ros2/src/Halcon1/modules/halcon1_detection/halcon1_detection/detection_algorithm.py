from halcon1_types import DetectionResult

class DetectionAlgorithm:
    def __init__(self):
        self.camera_width = 640
        self.camera_height = 480

    def detect(self, image = None) -> DetectionResult:
        # TODO: run YOLO model

        # Mock detection results
        x = 100
        y = 150
        width = 50
        height = 76

        return DetectionResult(x, y, width, height)