import abc
import inspect
from typing import (
    Any,
    Dict,
    Optional,
    Tuple,
)

from touchstone.bindings import (
    AnnotationHint,
    AutoBinding,
    ContextualBinding,
    NEW_EVERY_TIME,
    SINGLETON,
    SimpleBinding,
    TAbstract,
    TBinding,
    TConcrete,
)
from touchstone.exceptions import (
    BindingError,
    ResolutionError,
)

KwargsDict = Dict[str, Any]


class AbstractContainer(abc.ABC):
    @abc.abstractmethod
    def bind(self, abstract: TAbstract, concrete: TConcrete, lifetime_strategy: str) -> None:
        pass

    @abc.abstractmethod
    def bind_instance(self, abstract: TAbstract, instance: object) -> None:
        pass

    @abc.abstractmethod
    def bind_contextual(self, *,
                        when: TConcrete,
                        wants: Optional[TAbstract] = None,
                        called: Optional[str] = None,
                        give: TConcrete,
                        lifetime_strategy: str = NEW_EVERY_TIME
                        ) -> None:
        pass


class Container(AbstractContainer):
    """
    The `Container`. It supports binding and resolving dependencies.

    In intent, it binds abstract class `__init__` dependencies (declared via function annotations) to
    concrete implementations of those dependencies.

    What counts as an `abstract` is any hashable you might use as an annotation. For example:

        * An `abc.ABC` abstract base class
        * Any class
        * A string
        * A typehint using `typing

    What counts as a `concrete` is any callable that returns something that satisfies the dependency. For example:

        * A concrete implementation of an `abc.ABC`
        * A subclass
        * Any class
        * A lambda or function which acts as a factory function
        * A classmethod acting as a factory function
    """

    def __init__(self) -> None:
        self._bindings: Dict[TAbstract, TBinding] = {}
        self._instances: Dict[TBinding, Any] = {}
        self._contextual_bindings: Dict[Tuple[Optional[TAbstract], TAbstract, Optional[str]], ContextualBinding] = {}
        self.bind_instance(Container, self)

    def bind(self, abstract: TAbstract, concrete: TConcrete, lifetime_strategy: str = NEW_EVERY_TIME) -> None:
        """
        Bind an `abstract` (an annotation) to a `concrete` (something which returns objects fulfilling that annotation).
        If `lifetime_strategy` is set to `SINGLETON` then only one instance of the concrete implementation will be used.
        """
        self._bindings[abstract] = SimpleBinding(abstract, concrete, lifetime_strategy)

    def bind_instance(self, abstract: TAbstract, instance: Any) -> None:
        """
        A helper for binding an instance of an object as a singleton in the container.
        This is only useful if you've already created the singleton and want to bind it.
        If you have a method that returns a valid instance of the object, then use `bind` with
        `lifetime_strategy=SINGLETON` instead.
        """
        self.bind(abstract, lambda: instance, SINGLETON)

    def bind_contextual(self, *,
                        when: TConcrete,
                        wants: Optional[TAbstract] = None,
                        called: Optional[str] = None,
                        give: TConcrete,
                        lifetime_strategy: str = NEW_EVERY_TIME
                        ) -> None:
        """
        Used to create a *contextual* binding. This is used when you want to customize a specific class either by the
        `abstract` (annotation) it needs, or by the name of an `__init__` kwarg.
        """
        abstract = wants
        parent = when
        parent_name = called
        concrete = give
        self._contextual_bindings[(abstract, parent, parent_name)] = ContextualBinding(
            abstract=abstract,
            concrete=concrete,
            lifetime_strategy=lifetime_strategy,
            parent=parent,
            parent_name=parent_name,
        )

    def make(self, abstract: TAbstract, init_kwargs: Optional[KwargsDict] = None) -> Any:
        """
        Make an instance of `abstract` and return it, obeying registered binding rules.

        If `init_kwargs` is specified, it will overrule any bindings that have
        been registered and if `abstract` was registered as a singleton, the
        instance will NOT be saved as a singleton.

        `abstract` may also be any callable, so this could be used to call a
        function with automatic fulfillment of its args.
        """
        if init_kwargs is None:
            init_kwargs = {}
        return self._make(abstract, init_kwargs, None, None, AnnotationHint.NO_DEFAULT_VALUE)

    def _make(self,
              abstract: TAbstract,
              init_kwargs: KwargsDict,
              parent: Optional[TConcrete],
              parent_name: Optional[str],
              default_value: Any,
              ) -> Any:
        if init_kwargs == {} and abstract is None:
            return None

        if init_kwargs:
            binding = self._make_auto_binding(abstract, parent_name or str(abstract))
        else:
            binding = self._resolve_binding(abstract, parent, parent_name, default_value)

        if not init_kwargs and binding in self._instances:
            return self._instances[binding]

        # Build instance
        resolved_params = self._resolve_params(binding, init_kwargs)
        instance = binding.make(resolved_params)

        # Configure instance
        resolved_attrs = self._resolve_attrs(instance, binding, init_kwargs, resolved_params)
        for k, v in resolved_attrs.items():
            setattr(instance, k, v)

        used_kwarg_names = set(resolved_attrs.keys()) | set(resolved_params.keys())
        unused_init_kwargs = set(init_kwargs.keys()) - used_kwarg_names
        if unused_init_kwargs:
            raise ResolutionError(f"Unused explicit init_kwargs: {unused_init_kwargs}")

        if not init_kwargs and binding.lifetime_strategy == SINGLETON:
            self._instances[binding] = instance

        return instance

    def _resolve_binding(self,
                         abstract: TAbstract,
                         parent: Optional[TConcrete],
                         name: Optional[str],
                         default_value: Any,
                         ) -> TBinding:
        if parent is not None:
            binding = self._resolve_contextual_binding(abstract, parent, name)
            if binding:
                return binding

        binding = self._resolve_default_vaulue_binding(abstract, parent, name, default_value)
        if binding:
            return binding

        if abstract in self._bindings:
            return self._bindings[abstract]

        return self._make_auto_binding(abstract, name)

    def _make_auto_binding(self, abstract: TAbstract, name: Optional[str]) -> TBinding:
        try:
            return AutoBinding(abstract)
        except BindingError as e:
            raise ResolutionError(f"Can't resolve {name} requirement for {abstract}") from e

    def _resolve_default_vaulue_binding(self,
                                        abstract: TAbstract,
                                        parent: Optional[TConcrete],
                                        name: Optional[str],
                                        default_value: Any, ) -> Optional[TBinding]:
        if default_value is AnnotationHint.NO_DEFAULT_VALUE:
            return None

        return ContextualBinding(abstract=abstract,  # type: ignore
                                 concrete=lambda: default_value,
                                 lifetime_strategy=NEW_EVERY_TIME,
                                 parent=abstract,
                                 parent_name=name)

    # def __init__(self, abstract: Optional[TAbstract], concrete: TConcrete, lifetime_strategy: str,
    # parent: TConcrete, parent_name: Optional[str]) -> None:

    def _resolve_contextual_binding(self,
                                    abstract: TAbstract,
                                    parent: TAbstract,
                                    name: Optional[str],
                                    ) -> Optional[TBinding]:
        if abstract is inspect.Parameter.empty:
            abstract = None  # type: ignore  # None *IS* hashable, mypy!

        if (abstract, parent, name) in self._contextual_bindings:
            return self._contextual_bindings[(abstract, parent, name)]
        if (abstract, parent, None) in self._contextual_bindings:
            return self._contextual_bindings[(abstract, parent, None)]
        if (None, parent, name) in self._contextual_bindings:
            binding = self._contextual_bindings[(None, parent, name)]
            raise ResolutionError(f"{binding.parent} has contextual binding for param {binding.parent_name} but"
                                  " that binding is annotated as {abstract} and the contextual binding is missing "
                                  "the `wants` parameter")
        return None

    def _resolve_params(self, binding: TBinding, init_kwargs: KwargsDict) -> KwargsDict:
        needed_params = binding.get_concrete_params()
        resolved_params = {}
        for name, hint in needed_params.items():
            if name in init_kwargs:
                resolved_params[name] = init_kwargs[name]
            else:
                resolved_params[name] = self._make(hint.annotation, {},
                                                   parent=binding.concrete, parent_name=name,
                                                   default_value=hint.default_value)
        return resolved_params

    def _resolve_attrs(self,
                       instance: Any,
                       binding: TBinding,
                       init_kwargs: KwargsDict,
                       resolved_params: KwargsDict,
                       ) -> KwargsDict:
        needed_attrs = binding.get_concrete_attrs(instance)
        resolved_attrs = {}
        for name, hint in needed_attrs.items():
            if name in resolved_params:
                continue
            if name in init_kwargs:
                resolved_attrs[name] = init_kwargs[name]
            else:
                resolved_attrs[name] = self._make(hint.annotation, {},
                                                  parent=binding.concrete, parent_name=name,
                                                  default_value=hint.default_value)
        return resolved_attrs
