import abc
import builtins
import inspect
import typing
from dataclasses import dataclass
from typing import Any, Callable, Dict, Hashable, Optional, Tuple

from touchstone.exceptions import BindingError, ResolutionError

SINGLETON = "singleton"
NEW_EVERY_TIME = "new_every_time"

TAbstract = Hashable
TConcrete = Callable

BUILTIN_TYPES = {
    getattr(builtins, t) for t in dir(builtins) if isinstance(getattr(builtins, t), type)
}
TYPING_TYPES = {getattr(typing, t) for t in dir(typing) if isinstance(getattr(typing, t), type)}


def is_builtin(abstract: TAbstract) -> bool:
    return abstract in BUILTIN_TYPES


def is_typing(abstract: TAbstract) -> bool:
    return type(abstract) in TYPING_TYPES or abstract in TYPING_TYPES  # Needed for py37 typing.IO


def is_typing_classvar(obj: Any) -> bool:
    return (
        isinstance(obj, type(typing.ClassVar))  # py36
        or getattr(obj, "__origin__", None) is typing.ClassVar  # py37
    )


@dataclass
class AnnotationHint:
    annotation: TAbstract
    default_value: Any

    NO_DEFAULT_VALUE = inspect.Parameter.empty

    def has_default_value(self) -> bool:
        return self.default_value is not self.NO_DEFAULT_VALUE


class AbstractBinding(abc.ABC):
    abstract: Optional[TAbstract]
    concrete: TConcrete
    lifetime_strategy: str

    @abc.abstractmethod
    def is_contextual(self) -> bool:
        pass

    @abc.abstractmethod
    def __hash__(self) -> int:
        pass

    def make(self, fulfilled_params: Dict[str, Any]) -> Any:
        return self.concrete(**fulfilled_params)

    def get_concrete_params(self) -> Dict[str, AnnotationHint]:
        """
        Returns a dict for the concrete parameters, a dictionary carrying the kwarg-name to its annotation.
        """
        sig = inspect.signature(self.concrete)
        return {
            name: AnnotationHint(param.annotation, param.default)
            for name, param in sig.parameters.items()
            if param.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        }

    def get_concrete_attrs(self, instance: Any) -> Dict[str, AnnotationHint]:
        """
        Returns a dict for the concrete's attribute annotations, that is `self.concrete.__annotations__`.
        Excludes ClassVar typehints and excludes annotations that exist as attributes on the concrete class itself.
        """
        try:
            needed_attrs = {
                param: annotation
                for param, annotation in self.concrete.__annotations__.items()
                if self._is_needed_attr(param, annotation)
            }
            return {
                param: AnnotationHint(
                    annotation, getattr(instance, param, AnnotationHint.NO_DEFAULT_VALUE)
                )
                for param, annotation in needed_attrs.items()
            }
        except AttributeError:
            return {}

    def _is_needed_attr(self, param: str, annotation: TAbstract) -> bool:
        if param == "return":
            return False
        if hasattr(self.concrete, param):
            return False
        if is_typing_classvar(annotation):
            return False
        return True


class SimpleBinding(AbstractBinding):
    def __init__(self, abstract: TAbstract, concrete: TConcrete, lifetime_strategy: str) -> None:
        if is_builtin(abstract):
            raise BindingError(f"Cannot bind builtin type {abstract}")
        self.abstract = abstract
        self.concrete: TConcrete = concrete
        self.lifetime_strategy = lifetime_strategy

    def is_contextual(self) -> bool:
        return False

    def __hash__(self) -> int:
        return hash((self.abstract, self.concrete, self.lifetime_strategy))


class AutoBinding(AbstractBinding):
    lifetime_strategy = NEW_EVERY_TIME

    def __init__(self, abstract: TAbstract) -> None:
        if (
            not callable(abstract)
            or inspect.isabstract(abstract)
            or abstract is inspect.Parameter.empty
            or is_builtin(abstract)
            or is_typing(abstract)
        ):
            raise BindingError(f"Cannot create auto-binding for type {abstract}")
        self.abstract = abstract
        self.concrete: TConcrete = abstract

    def is_contextual(self) -> bool:
        return False

    def __hash__(self) -> int:
        return hash((self.abstract, self.concrete))


class ContextualBinding(AbstractBinding):
    def __init__(
        self,
        abstract: Optional[TAbstract],
        concrete: TConcrete,
        lifetime_strategy: str,
        parent: TConcrete,
        parent_name: Optional[str],
    ) -> None:
        if abstract is None and parent_name is None:
            raise BindingError(f"Cannot create contextual binding with no context for {parent}")
        self.abstract = abstract
        self.concrete: TConcrete = concrete
        self.lifetime_strategy = lifetime_strategy
        self.parent = parent
        self.parent_name = parent_name

    def is_contextual(self) -> bool:
        return True

    def __hash__(self) -> int:
        hash_data = (
            self.abstract,
            self.concrete,
            self.lifetime_strategy,
            self.parent,
            self.parent_name,
        )
        return hash(hash_data)


TBinding = typing.Union[AutoBinding, SimpleBinding, ContextualBinding]


class BindingResolver:
    def __init__(self) -> None:
        self._bindings: Dict[TAbstract, TBinding] = {}
        self._contextual_bindings: Dict[
            Tuple[Optional[TAbstract], TAbstract, Optional[str]], ContextualBinding
        ] = {}

    def bind(
        self, abstract: TAbstract, concrete: TConcrete, lifetime_strategy: str = NEW_EVERY_TIME
    ) -> None:
        """
        Bind an `abstract` (an annotation) to a `concrete` (something which returns objects fulfilling that annotation).
        If `lifetime_strategy` is set to `SINGLETON` then only one instance of the concrete implementation will be used.
        """
        self._bindings[abstract] = SimpleBinding(abstract, concrete, lifetime_strategy)

    def bind_contextual(
        self,
        *,
        when: TConcrete,
        wants: Optional[TAbstract] = None,
        wants_name: Optional[str] = None,
        give: TConcrete,
        lifetime_strategy: str = NEW_EVERY_TIME,
    ) -> None:
        """
        Used to create a *contextual* binding. This is used when you want to customize a specific class either by the
        `abstract` (annotation) it needs, or by the name of an `__init__` kwarg.
        """
        abstract = wants
        parent = when
        parent_name = wants_name
        concrete = give
        self._contextual_bindings[(abstract, parent, parent_name)] = ContextualBinding(
            abstract=abstract,
            concrete=concrete,
            lifetime_strategy=lifetime_strategy,
            parent=parent,
            parent_name=parent_name,
        )

    def resolve_binding(
        self,
        abstract: TAbstract,
        parent: Optional[TConcrete] = None,
        name: Optional[str] = None,
        default_value: Any = AnnotationHint.NO_DEFAULT_VALUE,
    ) -> TBinding:
        if parent is not None:
            binding = self._resolve_contextual_binding(abstract, parent, name)
            if binding:
                return binding

            binding = self._resolve_default_value_binding(abstract, parent, name, default_value)
            if binding:
                return binding

        if abstract in self._bindings:
            return self._bindings[abstract]

        return self.make_auto_binding(abstract, name, parent)

    def make_auto_binding(
        self, abstract: TAbstract, name: Optional[str], parent: Optional[TConcrete] = None
    ) -> TBinding:
        try:
            return AutoBinding(abstract)
        except BindingError as e:
            if parent is None:
                raise ResolutionError(f"Can't resolve {name}: {abstract}") from e
            else:
                raise ResolutionError(
                    f"Can't resolve {name}: {abstract}, which is required by {parent}"
                ) from e

    def _resolve_default_value_binding(
        self, abstract: TAbstract, parent: TConcrete, name: Optional[str], default_value: Any
    ) -> Optional[TBinding]:
        if default_value is AnnotationHint.NO_DEFAULT_VALUE:
            return None

        return ContextualBinding(
            abstract=abstract,
            concrete=lambda: default_value,
            lifetime_strategy=NEW_EVERY_TIME,
            parent=parent,
            parent_name=name,
        )

    # def __init__(self, abstract: Optional[TAbstract], concrete: TConcrete, lifetime_strategy: str,
    # parent: TConcrete, parent_name: Optional[str]) -> None:

    def _resolve_contextual_binding(
        self, abstract: TAbstract, parent: TAbstract, name: Optional[str]
    ) -> Optional[TBinding]:
        if abstract is inspect.Parameter.empty:
            abstract = None  # type: ignore  # None *IS* hashable, mypy!

        if (abstract, parent, name) in self._contextual_bindings:
            return self._contextual_bindings[(abstract, parent, name)]
        if (abstract, parent, None) in self._contextual_bindings:
            return self._contextual_bindings[(abstract, parent, None)]
        if (None, parent, name) in self._contextual_bindings:
            binding = self._contextual_bindings[(None, parent, name)]
            raise ResolutionError(
                f"{binding.parent} has contextual binding for param {binding.parent_name} but"
                f" that binding is annotated as {abstract} and the contextual binding is missing"
                f" the `wants` parameter"
            )
        return None
