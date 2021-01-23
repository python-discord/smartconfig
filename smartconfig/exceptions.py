class SmartconfigException(Exception):
    """Base exception of `smartconfig` library."""
    pass


class PathConflict(ValueError, SmartconfigException):
    """
    Two configuration entries point to the same path.

    Provide a `path` argument to the metaclass to bypass this restriction.
    """
    pass


class ConfigurationKeyError(AttributeError, SmartconfigException):
    """An invalid key name has been used."""
    pass


class InvalidOperation(RuntimeError, SmartconfigException):
    """An invalid operation has been performed."""
    pass


class ConfigurationError(ValueError, SmartconfigException):
    """The provided configuration is invalid."""
    pass
