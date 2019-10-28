from .middleware import InjectViewsMiddleware
from .properties import get_container, inject_magic_properties

__all__ = ["InjectViewsMiddleware", "inject_magic_properties", "get_container"]
