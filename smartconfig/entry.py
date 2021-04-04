from itertools import chain
from typing import Any, Dict, NoReturn, Optional, Tuple

from smartconfig import _registry
from smartconfig._registry import get_attribute, unload_defaults, used_paths
from smartconfig.exceptions import ConfigurationError, ConfigurationKeyError, InvalidOperation, PathConflict


class _ConfigEntryMeta(type):
    """
    Metaclass used to define special ConfigEntry behaviors.

    Note: Using this metaclass outside of the library is currently not supported.
    """

    def __getattribute__(cls, name: str) -> Optional[Any]:
        """
        Look up the attribute through the configuration system.

        If the attribute name starts with `_`, normal lookup is done, otherwise _registry.global_configuration is used.

        Args:
            name: Attribute to lookup

        Raises:
            ConfigurationKeyError: The attribute doesn't exist.
        """
        # Use the normal lookup for attribute starting with `_`
        if name.startswith('_'):
            return super().__getattribute__(name)

        return get_attribute(cls.__path, name)

    def __new__(cls, name: str, bases: Tuple[type, ...], dict_: Dict[str, Any], path: Optional[str] = None) -> type:
        """
        Add the `__defined_attributes` and `__path_override` attributes to the new entry.

        Args:
            path: Custom path used for this entry instead of the module name.
        """
        dict_[f"{cls.__name__}__path_override"] = path

        return super().__new__(cls, name, bases, dict_)

    def _register_entry(cls) -> None:
        """Set the `__path` attribute and register the entry."""
        cls.__path = cls.__path_override or cls.__module__
        if cls.__path in _registry.used_paths:
            raise PathConflict(f"An entry at {cls.__path!r} already exists.")  # TODO: Add an FAQ link.

        configuration = {
            key: value for key, value in cls.__dict__.items() if not key.startswith('_')
        }

        current_node = _registry.global_configuration

        for node_name in cls.__path.split("."):
            current_node = current_node.setdefault(node_name, {})

        for key, value in configuration.items():
            # We only write values that aren't already defined.
            if key not in current_node:
                current_node[key] = value

        used_paths.add(cls.__path)

    def _check_undefined_entries(cls) -> None:
        """Raise `ConfigurationKeyError` if any attribute doesn't have a defined value."""
        defined_attributes = [
            name for name in chain(cls.__dict__.keys(), getattr(cls, "__annotations__", ())) if not name.startswith('_')
        ]

        for attribute in defined_attributes:
            try:
                get_attribute(cls.__path, attribute)
            except (ConfigurationError, ConfigurationKeyError):
                raise ConfigurationKeyError(f"Attribute {attribute!r} doesn't have a defined value.") from None

    def __init__(cls, name: str, bases: Tuple[type, ...], dict_: Dict[str, Any], path: Optional[str] = None):
        """
        Initialize the new entry.

        Raises:
            PathConflict: An entry is already registered for this path. Use the `path` metaclass argument.
            ConfigurationKeyError: An attribute doesn't have a defined value.
        """
        super().__init__(name, bases, dict_)

        cls._register_entry()
        cls._check_undefined_entries()

    def __del__(cls) -> None:
        """Cleanup the defaults from the global configuration."""
        unload_defaults(cls.__path)

    def __repr__(cls) -> str:
        """Return a short representation of the entry."""
        if hasattr(cls, '__path'):
            return f"<_ConfigEntryMeta {cls.__name__} at {cls.__path!r}>"
        else:
            return f"<_ConfigEntryMeta {cls.__name__}>"

    def __eq__(cls, other: Any) -> bool:
        """Return true if this entry and the other point to the same path."""
        if not isinstance(other, _ConfigEntryMeta):
            return NotImplemented
        return cls.__path == other.__path


class ConfigEntry(metaclass=_ConfigEntryMeta):
    """
    Base class for new configuration entries.

    Class attributes of the subclasses can be overwritten using YAML configuration files.
    The entry will use its default values and potentially directly override them with already loaded configurations,
    and will also be overwritten in the future by newly loaded configurations.
    Attributes starting by an underscore (_) will be looked up through a normal class attribute lookup.

    The default path used by an entry is the name of the module it is defined in, or the `path` metaclass argument.
    """

    def __init__(self) -> NoReturn:
        """Raises `InvalidOperation` as creating instances isn't allowed."""
        raise InvalidOperation("Creating instances of ConfigEntry isn't allowed.")
