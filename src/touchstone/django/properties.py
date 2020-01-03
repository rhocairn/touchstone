from typing import Any, Optional, TypeVar

from django.conf import settings
from django.utils import module_loading
from touchstone import Container
from touchstone.bindings import AutoBinding, TAbstract


def get_container() -> Container:
    container: Container = module_loading.import_string(settings.TOUCHSTONE_CONTAINER_GETTER)()
    return container


class MagicProperty:
    """
    This descriptor uses the Touchstone container registered by Django (see `get_container` above)
    to resolve dependencies. For example:

        >>> class Child: pass
        >>> class Parent:
        >>>     obj = MagicProperty(abstract=Child, default_value=AnnotationHint.NO_DEFAULT_VALUE)
        >>> assert isinstance(Parent().obj, Child)
    """

    def __init__(self, abstract: TAbstract, default_value: Any) -> None:
        self.abstract = abstract
        self.default_value = default_value
        self.name: Optional[str] = None
        self.parent: Optional[type] = None

    def __set_name__(self, owner: type, name: str) -> None:
        if self.name is None and self.parent is None:
            self.name = name
            self.parent = owner
        elif name != self.name or owner is not self.parent:
            raise TypeError(
                f"Cannot assign MagicProperty to two different names ({self.name} and {name}) "
                f"or two parents ({self.parent} and {owner})"
            )

    def __get__(self, instance: Optional[object], cls: Optional[type] = None) -> Any:
        if not self.name:
            raise TypeError("This MagicProperty has not been assigned a name.")
        if instance is None:
            return self
        if self.name in instance.__dict__:
            return instance.__dict__[self.name]

        result = self._make()
        instance.__dict__[self.name] = result
        return result

    def _make(self) -> Any:
        if not self.parent:
            raise TypeError("This MagicProperty has not been assigned a parent.")
        container = get_container()
        return container._make(  # FIXME!!
            abstract=self.abstract,
            init_kwargs={},
            parent=self.parent,
            parent_name=self.name,
            default_value=self.default_value,
        )


TInjectedClass = TypeVar("TInjectedClass", bound=type)


def inject_magic_properties(concrete: TInjectedClass) -> TInjectedClass:
    """
    This decorator will take in a class (`concrete`), look at its class annotations
    for non-ClassVar annotations, and which do not have a value already assigned,
    and create the missing MagicProperty instance on the class. For exampple:

        >>> class Child: pass
        >>> @inject_magic_properties
        >>> class Parent:
        >>>     obj: Child
        >>> assert isinstance(Parent().obj, Child)
    """
    needed_attrs = AutoBinding(concrete).get_concrete_attrs(concrete)
    for name, hint in needed_attrs.items():
        prop = MagicProperty(abstract=hint.annotation, default_value=hint.default_value)
        prop.__set_name__(concrete, name)
        setattr(concrete, name, prop)
    return concrete
