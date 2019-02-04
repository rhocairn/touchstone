import inspect
from typing import (
    Any,
    Callable,
    Dict,
    Hashable,
    Optional,
)

SINGLETON = 'singleton'
NEW_EVERY_TIME = 'new_every_time'

TAbstract = Hashable
TConcrete = Callable


class Binding:
    def __init__(self, abstract: TAbstract, concrete: TConcrete, lifetime_strategy: str) -> None:
        if self._is_primitive(abstract):
            raise TypeError("Cannot automatically bind primitive type {}".format(abstract))
        self.abstract = abstract
        self.concrete = concrete
        self.lifetime_strategy = lifetime_strategy

    def is_contextual(self) -> bool:
        return False

    def make(self, fulfilled_params: Dict[str, Any]) -> Any:
        return self.concrete(**fulfilled_params)

    def get_concrete_params(self) -> Dict[str, Any]:
        sig = inspect.signature(self.concrete)
        return {
            name: param.annotation
            for name, param in sig.parameters.items()
            if param.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        }

    def _is_primitive(self, abstract: TAbstract):
        return abstract in {str, bytes, int, float, complex, dict, list, tuple}

    def __hash__(self):
        return hash(self._hash_tuple())

    def _hash_tuple(self):
        return (self.abstract, self.concrete)


class ContextualBinding(Binding):
    def __init__(self, abstract: Optional[TAbstract], concrete: TConcrete, lifetime_strategy: str,
                 parent: TAbstract, parent_name: Optional[str]) -> None:
        super().__init__(abstract, concrete, lifetime_strategy)
        self.parent = parent
        self.parent_name = parent_name

    def is_contextual(self) -> bool:
        return True

    def _hash_tuple(self):
        return (self.abstract, self.concrete, self.parent, self.parent_name)
