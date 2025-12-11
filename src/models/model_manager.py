"""
Base Model Manager for AI models.

Handles model initialization, device selection, and resource management.
"""

import os
import torch
from pathlib import Path
from typing import Optional, Literal
from abc import ABC, abstractmethod

from core.config import Config
from utils.logger import setup_logger


logger = setup_logger()


class ModelManager(ABC):
    """
    Base class for AI model management.
    
    Handles:
    - Device selection (CPU/CUDA/MPS)
    - Model loading and caching
    - Resource cleanup
    """
    
    def __init__(self, config: Config):
        """
        Initialize model manager.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.device = self._get_device()
        self.model = None
        self.is_loaded = False
        
        logger.info(f"Model manager initialized on device: {self.device}")
    
    def _get_device(self) -> torch.device:
        """
        Automatically detect and select the best available device.
        
        Returns:
            torch.device: Selected device (cuda/mps/cpu)
        """
        use_gpu = self.config.get('use_gpu', True)
        
        if not use_gpu:
            logger.info("GPU disabled by config, using CPU")
            return torch.device('cpu')
        
        # Check for CUDA (NVIDIA)
        if torch.cuda.is_available():
            device = torch.device('cuda')
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"Using CUDA device: {gpu_name}")
            return device
        
        # Check for MPS (Apple Silicon)
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device = torch.device('mps')
            logger.info("Using Apple MPS device")
            return device
        
        # Fallback to CPU
        logger.info("No GPU available, using CPU")
        return torch.device('cpu')
    
    @abstractmethod
    def load_model(self):
        """Load the AI model. Must be implemented by subclass."""
        pass
    
    @abstractmethod
    def unload_model(self):
        """Unload the AI model and free resources."""
        pass
    
    def get_model_cache_dir(self) -> Path:
        """
        Get the directory for caching models.
        
        Returns:
            Path to model cache directory
        """
        cache_dir = Path(self.config.get('models_dir'))
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.is_loaded and self.model is not None
    
    def get_device_info(self) -> dict:
        """
        Get information about the current device.
        
        Returns:
            Dict with device information
        """
        info = {
            'device_type': str(self.device),
            'gpu_available': torch.cuda.is_available(),
        }
        
        if torch.cuda.is_available():
            info['gpu_name'] = torch.cuda.get_device_name(0)
            info['gpu_memory_total'] = torch.cuda.get_device_properties(0).total_memory / 1e9  # GB
            info['gpu_memory_allocated'] = torch.cuda.memory_allocated(0) / 1e9  # GB
        
        return info
    
    def cleanup(self):
        """Clean up resources."""
        if self.is_model_loaded():
            self.unload_model()
        
        # Clear CUDA cache if using GPU
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.debug("Cleared CUDA cache")
