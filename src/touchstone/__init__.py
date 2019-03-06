from .version import __version__
from touchstone.container import (
    Container,
    SINGLETON,
    NEW_EVERY_TIME,
)

__all__ = ['__version__', 'Container', 'SINGLETON', 'NEW_EVERY_TIME']
