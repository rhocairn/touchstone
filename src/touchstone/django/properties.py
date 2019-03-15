from typing import (
    Any,
    Callable,
)

from django.utils.functional import cached_property
from django.views import View

from touchstone import Container
from touchstone.bindings import (
    TAbstract,
    TConcrete,
)


class MagicInjectedProperties:
    def __init__(self, container: Container):
        self.container = container

    def set_magic_properties(self, concrete: TConcrete) -> TConcrete:
        binding = self.container.bindings.resolve_binding(concrete)
        needed_attrs = binding.get_concrete_attrs(concrete)
        for name, hint in needed_attrs.items():
            prop = self._make_property(hint.annotation, binding.concrete, name, hint.default_value)
            setattr(concrete, name, cached_property(prop, name))
        return concrete

    def _make_property(self, abstract: TAbstract, parent: TConcrete, name: str, default_value: Any) -> Callable:
        container = self.container

        def prop(self: View) -> Any:
            return container._make(  # FIXME!!
                abstract=abstract,
                init_kwargs={},
                parent=parent,
                parent_name=name,
                default_value=default_value,
            )

        prop.__name__ = name
        return prop
