"""
Model Architecture Extensions for Detection Package

This module automatically registers custom neural network architectures with ultralytics YOLO.
Simply importing this module enables support for models trained with custom blocks.

Usage:
    from . import extensions  # Automatically registers all extensions

Supported Extensions:
    - LMWP-YOLO: Long-range drone detection architecture with MAFR blocks
"""

import ultralytics.nn.modules.block as block_module


def _register_extensions():
    """
    Automatically register all model architecture extensions with ultralytics.

    This function patches the ultralytics.nn.modules.block module to include
    custom blocks, allowing models trained with these architectures to load seamlessly.
    """
    try:
        # Import LMWP-YOLO blocks
        from .lmwp_yolo import __all__ as lmwp_exports
        from . import lmwp_yolo

        # Register each block with ultralytics
        for block_name in lmwp_exports:
            if not hasattr(block_module, block_name):
                setattr(block_module, block_name, getattr(lmwp_yolo, block_name))

        # Update __all__ to include extensions
        if hasattr(block_module, '__all__'):
            original_all = list(block_module.__all__)
            block_module.__all__ = tuple(set(original_all + list(lmwp_exports)))

    except Exception as e:
        # Fail silently - extensions are optional
        # Standard YOLO models will still work
        import warnings
        warnings.warn(f"Could not load model extensions: {e}. Standard models will work normally.")


# Auto-register extensions when this module is imported
_register_extensions()
