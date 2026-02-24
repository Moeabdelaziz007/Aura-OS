"""
Aether Configuration Loader Module

This module provides comprehensive configuration loading, validation, and hot-reload
capabilities for the AetherOS system. It handles JSON-based configuration files with
schema validation, type checking, and automatic file watching for hot-reload support.

Classes:
    ConfigValidationError: Exception raised when configuration validation fails.
    ConfigLoadError: Exception raised when configuration loading fails.
    AetherConfigLoader: Main configuration loader class with hot-reload support.

Example:
    >>> loader = AetherConfigLoader()
    >>> config = loader.load_config("config/aether_config.json")
    >>> loader.enable_hot_reload(callback=lambda cfg: print("Config reloaded!"))
"""

import json
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
from dataclasses import dataclass, field
from datetime import datetime
import hashlib


T = TypeVar('T', bound='AetherConfig')


class ConfigValidationError(Exception):
    """Exception raised when configuration validation fails.
    
    Attributes:
        message: Error message describing the validation failure.
        path: JSON path to the invalid configuration value.
        value: The invalid value that caused the validation error.
    """
    
    def __init__(self, message: str, path: str = "", value: Any = None) -> None:
        """Initialize ConfigValidationError.
        
        Args:
            message: Error message describing the validation failure.
            path: JSON path to the invalid configuration value.
            value: The invalid value that caused the validation error.
        """
        self.message = message
        self.path = path
        self.value = value
        full_message = f"Validation error at '{path}': {message}" if path else message
        super().__init__(full_message)


class ConfigLoadError(Exception):
    """Exception raised when configuration loading fails.
    
    Attributes:
        message: Error message describing the load failure.
        file_path: Path to the configuration file that failed to load.
        cause: Original exception that caused the load error.
    """
    
    def __init__(self, message: str, file_path: str = "", cause: Optional[Exception] = None) -> None:
        """Initialize ConfigLoadError.
        
        Args:
            message: Error message describing the load failure.
            file_path: Path to the configuration file that failed to load.
            cause: Original exception that caused the load error.
        """
        self.message = message
        self.file_path = file_path
        self.cause = cause
        full_message = f"Failed to load config from '{file_path}': {message}" if file_path else message
        super().__init__(full_message)


@dataclass
class SchemaField:
    """Represents a field schema for configuration validation.
    
    Attributes:
        name: Field name in the configuration.
        type: Expected Python type for the field.
        required: Whether the field is required.
        default: Default value if field is optional and not present.
        validator: Optional custom validator function for the field.
    """
    
    name: str
    type: Type[Any]
    required: bool = True
    default: Any = None
    validator: Optional[Callable[[Any], bool]] = None


@dataclass
class AetherConfig:
    """Base configuration data class for AetherOS.
    
    This class provides a structured representation of AetherOS configuration
    with support for schema validation and type checking.
    
    Attributes:
        aether_version: Version string of the AetherOS configuration.
        config_path: Path to the configuration file.
        last_modified: Timestamp of last configuration modification.
        checksum: SHA256 checksum of the configuration content.
    """
    
    aether_version: str = "1.0.0"
    config_path: str = ""
    last_modified: Optional[datetime] = None
    checksum: str = ""
    
    def __post_init__(self) -> None:
        """Post-initialization processing."""
        if not self.last_modified:
            self.last_modified = datetime.utcnow()
    
    def calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate SHA256 checksum of configuration data.
        
        Args:
            data: Configuration dictionary to checksum.
            
        Returns:
            Hexadecimal SHA256 checksum string.
        """
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of the configuration.
        """
        result: Dict[str, Any] = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result


@dataclass
class AetherConfigSchema:
    """Schema definition for AetherOS configuration validation.
    
    This class defines the expected structure and types for AetherOS
    configuration files, enabling automatic validation and type checking.
    
    Attributes:
        version_schema: Schema for version field.
        modules_schema: Schema for modules configuration.
        evolution_schema: Schema for evolution configuration.
        voice_schema: Schema for voice engine configuration.
        vision_schema: Schema for vision engine configuration.
        reasoning_schema: Schema for reasoning engine configuration.
        swarm_schema: Schema for swarm controller configuration.
        safety_schema: Schema for safety engine configuration.
        memory_schema: Schema for memory system configuration.
    """
    
    fields: List[SchemaField] = field(default_factory=lambda: [
        SchemaField("aether_version", str, required=True),
        SchemaField("aether_modules", list, required=True),
        SchemaField("aether_evolution", dict, required=True),
        SchemaField("voice_engine", dict, required=True),
        SchemaField("vision_engine", dict, required=True),
        SchemaField("reasoning_engine", dict, required=True),
        SchemaField("swarm_controller", dict, required=True),
        SchemaField("safety_engine", dict, required=True),
        SchemaField("memory_system", dict, required=True),
    ])


class AetherConfigLoader:
    """Main configuration loader class with hot-reload support.
    
    This class provides comprehensive configuration loading capabilities including:
    - JSON file parsing with error handling
    - Schema validation and type checking
    - Hot-reload support via file watching
    - Configuration caching and checksum verification
    
    Attributes:
        config_dir: Directory containing configuration files.
        configs: Dictionary of loaded configurations by name.
        schemas: Dictionary of schema definitions by config name.
        _watch_thread: Background thread for file watching.
        _watch_running: Flag indicating if file watching is active.
        _reload_callbacks: List of callbacks to invoke on config reload.
        _file_timestamps: Dictionary of last modification timestamps.
        _lock: Thread lock for thread-safe operations.
    
    Example:
        >>> loader = AetherConfigLoader()
        >>> config = loader.load_config("aether_config.json")
        >>> loader.enable_hot_reload(callback=lambda cfg: print("Reloaded!"))
    """
    
    DEFAULT_CONFIG_DIR = "config"
    
    def __init__(self, config_dir: Optional[str] = None) -> None:
        """Initialize AetherConfigLoader.
        
        Args:
            config_dir: Directory containing configuration files. Defaults to "config".
        """
        self.config_dir = Path(config_dir or self.DEFAULT_CONFIG_DIR)
        self.configs: Dict[str, Dict[str, Any]] = {}
        self.schemas: Dict[str, AetherConfigSchema] = {
            "aether_config.json": AetherConfigSchema(),
            "aether_skills.json": AetherConfigSchema(),  # Uses same base schema
        }
        self._watch_thread: Optional[threading.Thread] = None
        self._watch_running = False
        self._reload_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        self._file_timestamps: Dict[str, float] = {}
        self._lock = threading.RLock()
        
        # Initialize schemas for different config files
        self._init_schemas()
    
    def _init_schemas(self) -> None:
        """Initialize validation schemas for different configuration files."""
        # Aether skills schema
        skills_fields = [
            SchemaField("skill_registry", dict, required=True),
            SchemaField("skill_promotion_criteria", dict, required=True),
            SchemaField("skill_consolidation", dict, required=True),
            SchemaField("skill_categories", list, required=True),
            SchemaField("skill_lifecycle", dict, required=True),
            SchemaField("skill_metrics", dict, required=True),
        ]
        self.schemas["aether_skills.json"] = AetherConfigSchema(fields=skills_fields)
    
    def load_config(
        self,
        config_name: str,
        validate: bool = True,
        cache: bool = True
    ) -> Dict[str, Any]:
        """Load configuration from JSON file.
        
        Args:
            config_name: Name of the configuration file (e.g., "aether_config.json").
            validate: Whether to validate the configuration against schema.
            cache: Whether to cache the loaded configuration.
            
        Returns:
            Dictionary containing the loaded configuration.
            
        Raises:
            ConfigLoadError: If the configuration file cannot be loaded.
            ConfigValidationError: If the configuration fails validation.
        """
        config_path = self.config_dir / config_name
        
        if not config_path.exists():
            raise ConfigLoadError(
                f"Configuration file not found",
                file_path=str(config_path)
            )
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigLoadError(
                f"Invalid JSON syntax: {e.msg}",
                file_path=str(config_path),
                cause=e
            ) from e
        except IOError as e:
            raise ConfigLoadError(
                f"Failed to read file: {str(e)}",
                file_path=str(config_path),
                cause=e
            ) from e
        
        # Validate configuration if requested
        if validate:
            self._validate_config(config_data, config_name)
        
        # Store file timestamp for hot-reload
        self._file_timestamps[config_name] = config_path.stat().st_mtime
        
        # Cache configuration if requested
        if cache:
            with self._lock:
                self.configs[config_name] = config_data
        
        return config_data
    
    def _validate_config(
        self,
        config_data: Dict[str, Any],
        config_name: str
    ) -> None:
        """Validate configuration against schema.
        
        Args:
            config_data: Configuration dictionary to validate.
            config_name: Name of the configuration file.
            
        Raises:
            ConfigValidationError: If the configuration fails validation.
        """
        schema = self.schemas.get(config_name)
        
        if schema is None:
            # No schema defined, skip validation
            return
        
        for field in schema.fields:
            field_path = f"{config_name}.{field.name}"
            
            # Check if required field is present
            if field.required and field.name not in config_data:
                raise ConfigValidationError(
                    f"Required field '{field.name}' is missing",
                    path=field_path
                )
            
            # Skip validation if field is optional and not present
            if not field.required and field.name not in config_data:
                continue
            
            value = config_data[field.name]
            
            # Type checking
            if not isinstance(value, field.type):
                # Handle Union types (e.g., Union[str, int])
                if hasattr(field.type, "__origin__") and field.type.__origin__ is Union:
                    type_args = field.type.__args__
                    if not isinstance(value, type_args):
                        raise ConfigValidationError(
                            f"Expected type {field.type}, got {type(value).__name__}",
                            path=field_path,
                            value=value
                        )
                else:
                    raise ConfigValidationError(
                        f"Expected type {field.type.__name__}, got {type(value).__name__}",
                        path=field_path,
                        value=value
                    )
            
            # Custom validator
            if field.validator is not None and not field.validator(value):
                raise ConfigValidationError(
                    f"Custom validation failed for field '{field.name}'",
                    path=field_path,
                    value=value
                )
    
    def get_config(self, config_name: str) -> Dict[str, Any]:
        """Get cached configuration by name.
        
        Args:
            config_name: Name of the configuration file.
            
        Returns:
            Cached configuration dictionary.
            
        Raises:
            ConfigLoadError: If the configuration is not loaded.
        """
        with self._lock:
            if config_name not in self.configs:
                raise ConfigLoadError(
                    f"Configuration '{config_name}' not loaded. "
                    f"Call load_config() first."
                )
            return self.configs[config_name].copy()
    
    def reload_config(self, config_name: str) -> Dict[str, Any]:
        """Reload configuration from file.
        
        Args:
            config_name: Name of the configuration file to reload.
            
        Returns:
            Reloaded configuration dictionary.
            
        Raises:
            ConfigLoadError: If the configuration cannot be reloaded.
        """
        config_data = self.load_config(config_name, validate=True, cache=True)
        
        # Invoke reload callbacks
        for callback in self._reload_callbacks:
            try:
                callback(config_name, config_data)
            except Exception as e:
                # Log error but don't fail the reload
                print(f"Warning: Reload callback failed: {e}")
        
        return config_data
    
    def enable_hot_reload(
        self,
        check_interval: float = 1.0,
        callback: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ) -> None:
        """Enable hot-reload by watching configuration files for changes.
        
        Args:
            check_interval: Interval in seconds between file checks.
            callback: Optional callback function to invoke on reload.
                      Receives (config_name, config_data) as arguments.
        """
        if self._watch_running:
            return
        
        if callback is not None:
            self._reload_callbacks.append(callback)
        
        self._watch_running = True
        self._watch_thread = threading.Thread(
            target=self._watch_files,
            args=(check_interval,),
            daemon=True
        )
        self._watch_thread.start()
    
    def disable_hot_reload(self) -> None:
        """Disable hot-reload and stop file watching."""
        self._watch_running = False
        if self._watch_thread is not None:
            self._watch_thread.join(timeout=5.0)
            self._watch_thread = None
    
    def _watch_files(self, check_interval: float) -> None:
        """Background thread function to watch for file changes.
        
        Args:
            check_interval: Interval in seconds between file checks.
        """
        while self._watch_running:
            try:
                for config_name in self._file_timestamps:
                    config_path = self.config_dir / config_name
                    
                    if not config_path.exists():
                        continue
                    
                    current_mtime = config_path.stat().st_mtime
                    last_mtime = self._file_timestamps.get(config_name, 0)
                    
                    if current_mtime > last_mtime:
                        try:
                            self.reload_config(config_name)
                        except Exception as e:
                            print(f"Warning: Failed to reload '{config_name}': {e}")
                
                time.sleep(check_interval)
            except Exception as e:
                print(f"Warning: File watcher error: {e}")
                time.sleep(check_interval)
    
    def add_reload_callback(
        self,
        callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """Add a callback to be invoked on configuration reload.
        
        Args:
            callback: Callback function receiving (config_name, config_data).
        """
        self._reload_callbacks.append(callback)
    
    def remove_reload_callback(
        self,
        callback: Callable[[str, Dict[str, Any]], None]
    ) -> None:
        """Remove a reload callback.
        
        Args:
            callback: Callback function to remove.
        """
        if callback in self._reload_callbacks:
            self._reload_callbacks.remove(callback)
    
    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all loaded configurations.
        
        Returns:
            Dictionary mapping config names to their configuration data.
        """
        with self._lock:
            return {name: data.copy() for name, data in self.configs.items()}
    
    def clear_cache(self) -> None:
        """Clear all cached configurations."""
        with self._lock:
            self.configs.clear()
            self._file_timestamps.clear()
    
    def validate_json_syntax(self, config_path: str) -> bool:
        """Validate JSON syntax of a configuration file.
        
        Args:
            config_path: Path to the configuration file.
            
        Returns:
            True if JSON syntax is valid, False otherwise.
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except (json.JSONDecodeError, IOError):
            return False


# Global configuration loader instance
_global_loader: Optional[AetherConfigLoader] = None
_loader_lock = threading.RLock()


def get_global_loader() -> AetherConfigLoader:
    """Get the global configuration loader instance.
    
    Creates a new instance if one doesn't exist.
    
    Returns:
        The global AetherConfigLoader instance.
    """
    global _global_loader
    
    with _loader_lock:
        if _global_loader is None:
            _global_loader = AetherConfigLoader()
        return _global_loader


def load_aether_config(config_name: str = "aether_config.json") -> Dict[str, Any]:
    """Load AetherOS configuration using the global loader.
    
    Args:
        config_name: Name of the configuration file.
        
    Returns:
        Configuration dictionary.
        
    Raises:
        ConfigLoadError: If the configuration cannot be loaded.
        ConfigValidationError: If the configuration fails validation.
    """
    loader = get_global_loader()
    return loader.load_config(config_name)


def load_skills_config(config_name: str = "aether_skills.json") -> Dict[str, Any]:
    """Load AetherOS skills configuration using the global loader.
    
    Args:
        config_name: Name of the skills configuration file.
        
    Returns:
        Skills configuration dictionary.
        
    Raises:
        ConfigLoadError: If the configuration cannot be loaded.
        ConfigValidationError: If the configuration fails validation.
    """
    loader = get_global_loader()
    return loader.load_config(config_name)
