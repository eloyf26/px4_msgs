# Model Architecture Extensions

This directory contains custom neural network architectures that extend ultralytics YOLO.

## What are Extensions?

Extensions are custom neural network blocks that allow you to:
- Load models trained with specialized architectures
- Add new detection capabilities without modifying core code
- Experiment with state-of-the-art computer vision techniques

## Current Extensions

### LMWP-YOLO (`lmwp_yolo.py`)

Architecture for long-range small drone detection in challenging conditions.

**Reference:** "Improved YOLO for long range detection of small drones" - Nature Scientific Reports

**Key Components:**
- **MAFR**: Multi-scale Adaptive Feature Refinement - enhances small object features
- **MCALayer**: Multi-dimensional Collaborative Attention - improves feature discrimination
- **PP-LCNet Backbone**: Lightweight CPU-optimized backbone for efficient inference

**Use Case:** Detecting small drones at long distances (200m+) in cluttered backgrounds

## How It Works

Extensions are **automatically registered** when the detection package loads:

```python
# In your code - no manual setup needed!
from detection import DetectionAlgorithm

# Extensions are already registered
algorithm = DetectionAlgorithm()  # Can now load LMWP-YOLO models
```

### Behind the Scenes

1. Detection package imports: `from . import extensions`
2. `extensions/__init__.py` automatically patches ultralytics with custom blocks
3. Models with custom architectures load seamlessly

**No configuration required** - it just works!

## Adding New Extensions

To add a new architecture:

1. **Create module file**: `extensions/my_architecture.py`
2. **Define blocks**: Implement your custom nn.Module classes
3. **Export**: Add block names to `__all__`
4. **Register**: Update `extensions/__init__.py` to import your module

Example:

```python
# extensions/my_architecture.py
import torch.nn as nn

__all__ = ['MyCustomBlock']

class MyCustomBlock(nn.Module):
    def __init__(self, c1, c2):
        super().__init__()
        self.conv = nn.Conv2d(c1, c2, 3, padding=1)

    def forward(self, x):
        return self.conv(x)
```

```python
# extensions/__init__.py
from .lmwp_yolo import __all__ as lmwp_exports
from .my_architecture import __all__ as my_exports  # Add this

# Register all
for block_name in lmwp_exports + my_exports:  # Include new exports
    setattr(block_module, block_name, getattr(module, block_name))
```

## Model Compatibility

### Standard YOLO Models
✅ Work without any extensions (yolo11n.pt, yolov8s.pt, etc.)

### Custom Architecture Models
✅ Automatically supported if extension exists (lmwp-yolo.pt, etc.)
❌ Will fail if trained with blocks not in extensions/

### Checking Model Requirements

To see what blocks a model uses:

```python
import torch
checkpoint = torch.load('model.pt')
print(checkpoint['model'])  # Shows architecture
```

## Troubleshooting

### "Can't get attribute 'MyBlock'" Error

**Cause:** Model was trained with a custom block not in extensions/

**Solution:** Add the missing block to an extension file

### Extensions Not Loading

Check logs for warnings:
```
Could not load model extensions: <error>
```

Standard YOLO models will still work, but custom models won't.

## Best Practices

1. **Keep extensions modular** - One architecture per file
2. **Document thoroughly** - Explain what each block does
3. **Test compatibility** - Ensure blocks work with ultralytics YOLO
4. **Version carefully** - Note ultralytics version compatibility

## References

- LMWP-YOLO Paper: https://www.nature.com/articles/...
- Ultralytics Documentation: https://docs.ultralytics.com
- PP-LCNet Paper: https://arxiv.org/abs/...
