"""
Configuration loader for hybrid JSON/Python config system

Loads JSON overrides and merges with Python dataclass defaults.
"""

import json
import os
import carb
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigLoader:
  """Loads and merges JSON config with Python defaults."""
  
  _config_cache: Optional[Dict[str, Any]] = None
  _config_path: Optional[str] = None
  
  @classmethod
  def get_config_path(cls) -> str:
    """Get the path to tendroids_config.json."""
    if cls._config_path is None:
      # Get the directory of this file
      current_dir = Path(__file__).parent
      cls._config_path = str(current_dir / "tendroids_config.json")
    return cls._config_path
  
  @classmethod
  def load_json(cls) -> Dict[str, Any]:
    """
    Load JSON config file, with caching.
    
    Returns:
        Dict of config values, or empty dict if file doesn't exist
    """
    if cls._config_cache is not None:
      return cls._config_cache
    
    config_path = cls.get_config_path()
    
    if not os.path.exists(config_path):
      carb.log_warn(
        f"[ConfigLoader] Config file not found: {config_path}. "
        f"Using Python defaults."
      )
      cls._config_cache = {}
      return cls._config_cache
    
    try:
      with open(config_path, 'r') as f:
        cls._config_cache = json.load(f)
      carb.log_info(f"[ConfigLoader] Loaded config from: {config_path}")
      return cls._config_cache
    
    except json.JSONDecodeError as e:
      carb.log_error(
        f"[ConfigLoader] Invalid JSON in config file: {e}. "
        f"Using Python defaults."
      )
      cls._config_cache = {}
      return cls._config_cache
    
    except Exception as e:
      carb.log_error(f"[ConfigLoader] Failed to load config: {e}")
      cls._config_cache = {}
      return cls._config_cache
  
  @classmethod
  def reload(cls) -> Dict[str, Any]:
    """Force reload of config from disk."""
    cls._config_cache = None
    return cls.load_json()
  
  @classmethod
  def merge_with_dataclass(cls, dataclass_instance, json_section: str, **overrides):
    """
    Merge JSON config section into dataclass instance.
    
    Args:
        dataclass_instance: The dataclass to update
        json_section: Top-level key in JSON (e.g., "sea_floor")
        **overrides: Additional explicit overrides (highest priority)
    
    Returns:
        Updated dataclass instance
    """
    config = cls.load_json()
    
    # Get JSON section
    json_values = config.get(json_section, {})
    
    # Merge: Python defaults < JSON < explicit overrides
    for field_name in dataclass_instance.__dataclass_fields__:
      # Priority 1: Explicit override
      if field_name in overrides:
        setattr(dataclass_instance, field_name, overrides[field_name])
      # Priority 2: JSON value
      elif field_name in json_values:
        value = json_values[field_name]
        # Convert lists to tuples if needed
        if isinstance(value, list):
          current_value = getattr(dataclass_instance, field_name)
          if isinstance(current_value, tuple):
            value = tuple(value)
        setattr(dataclass_instance, field_name, value)
      # Priority 3: Keep Python default (already set)
    
    return dataclass_instance
  
  @classmethod
  def get_value(cls, *path, default=None):
    """
    Get a specific value from config using path notation.
    
    Args:
        *path: Nested keys (e.g., "tendroid_geometry", "flare_height_percent")
        default: Value to return if not found
    
    Returns:
        Config value or default
    
    Example:
        ConfigLoader.get_value("tendroid_animation", "wave_speed", default=40.0)
    """
    config = cls.load_json()
    
    current: Any = config
    for key in path:
      if isinstance(current, dict) and key in current:
        current = current[key]
      else:
        return default
    
    return current


# Module-level convenience function
def get_config_value(*path, default=None):
  """Get config value using path notation."""
  return ConfigLoader.get_value(*path, default=default)
