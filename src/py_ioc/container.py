import abc
import inspect
from typing import (  # noqa: F401
    Any,
    Dict,
    Optional,
    Tuple,
)

from py_ioc.bindings import (
    AbstractBinding,
    AutoBinding,
    Binding,
    ContextualBinding,
    NEW_EVERY_TIME,
    SINGLETON,
    TAbstract,
    TConcrete,
)


class AbstractContainer(abc.ABC):
    @abc.abstractmethod
    def bind(self, abstract: TAbstract, concrete: TConcrete, lifetime_strategy: str) -> None:
        pass

    @abc.abstractmethod
    def bind_instance(self, abstract: TAbstract, instance: object) -> None:
        pass

    @abc.abstractmethod
    def bind_contextual(self, *,
                        when: TAbstract,
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

    def __init__(self):
        self._bindings = {}  # type: Dict[TAbstract, Binding]
        self._instances = {}  # type: Dict[AbstractBinding, Any]
        self._contextual_bindings = {}  # type: Dict[Tuple[Optional[TAbstract], TAbstract, Optional[str]], ContextualBinding]  # noqa: E501
        self.bind_instance(Container, self)

    def bind(self, abstract: TAbstract, concrete: TConcrete, lifetime_strategy=NEW_EVERY_TIME) -> None:
        """
        Bind an `abstract` (an annotation) to a `concrete` (something which returns objects fulfilling that annotation).
        If `lifetime_strategy` is set to `SINGLETON` then only one instance of the concrete implementation will be used.
        """
        self._bindings[abstract] = Binding(abstract, concrete, lifetime_strategy)

    def bind_instance(self, abstract: TAbstract, instance: object) -> None:
        """
        A helper for binding an instance of an object as a singleton in the container.
        This is only useful if you've already created the singleton and want to bind it.
        If you have a method that returns a valid instance of the object, then use `bind` with
        `lifetime_strategy=SINGLETON` instead.
        """
        self._bindings[abstract] = Binding(abstract, lambda: instance, SINGLETON)

    def bind_contextual(self, *,
                        when: TAbstract,
                        wants: Optional[TAbstract] = None,
                        called: Optional[str] = None,
                        give: TConcrete,
                        lifetime_strategy: str = NEW_EVERY_TIME
                        ) -> None:
        """
        Used to create a *contextual* binding. This is used when you want to customize a specific class either by the
        `abstract` (annotation) it needs, or by the name of an `__init__` kwarg.
        """
        if wants is None and called is None:
            raise TypeError("Cannot create contextual binding with specifying either `wants` or `called`.")
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

    def make(self, abstract: TAbstract, init_kwargs: dict = None) -> Any:
        """
        Make an instance of `abstract` and return it, obeying registered binding rules.

        If `init_kwargs` is specified, it will overrule any bindings that have
        been registered and if `abstract` was registered as a singleton, the
        instance will NOT be saved as a singleton.

        `abstract` may also be any callable, so this could be used to call a
        function with automatic fulfillment of its args.
        """
        return self._make(abstract, init_kwargs, None, None)

    def _make(self,
              abstract: TAbstract,
              init_kwargs: dict,
              parent: Optional[TAbstract],
              parent_name: Optional[str],
              ) -> Any:
        if init_kwargs is None:
            init_kwargs = {}

        if init_kwargs:
            binding = self._make_auto_binding(abstract)
        else:
            binding = self._resolve_binding(abstract, parent, parent_name)

        if not init_kwargs and binding in self._instances:
            return self._instances[binding]

        fulfilled_params = self._resolve_params(binding, init_kwargs)
        instance = binding.make(fulfilled_params)

        if not init_kwargs and binding.lifetime_strategy == SINGLETON:
            self._instances[binding] = instance
        return instance

    def _resolve_binding(self,
                         abstract: Optional[TAbstract],
                         parent: Optional[TAbstract],
                         name: Optional[str],
                         ) -> AbstractBinding:
        if parent is not None:
            binding = self._resolve_contextual_binding(abstract, parent, name)
            if binding:
                return binding

        if abstract in self._bindings:
            return self._bindings[abstract]

        try:
            return self._make_auto_binding(abstract)
        except TypeError:
            raise TypeError("Can't fulfill parameter {}.{}: {}".format(parent, name, abstract))

    def _make_auto_binding(self, abstract: TAbstract) -> AutoBinding:
        if callable(abstract) and not inspect.isabstract(abstract):
            return AutoBinding(abstract, abstract)
        raise TypeError("Can't fulfill binding for {}".format(abstract))

    def _resolve_contextual_binding(self, abstract, parent, name):
        if abstract is inspect._empty:
            abstract = None
        if (abstract, parent, name) in self._contextual_bindings:
            return self._contextual_bindings[(abstract, parent, name)]
        if (abstract, parent, None) in self._contextual_bindings:
            return self._contextual_bindings[(abstract, parent, None)]
        if (None, parent, name) in self._contextual_bindings:
            binding = self._contextual_bindings[(None, parent, name)]
            if abstract is not None:
                raise TypeError("{}.{}: {} is annotated, but the contextual binding does not use type hints".format(
                    binding.abstract,
                    binding.parent_name,
                    abstract,
                ))
            return binding

    def _resolve_params(self, binding: AbstractBinding, init_kwargs: Dict[str, Any]):
        needed_params = binding.get_concrete_params()
        fulfilled_params = {}
        for name, annotation in needed_params.items():
            if name in init_kwargs:
                fulfilled_params[name] = init_kwargs[name]
            else:
                fulfilled_params[name] = self._make(annotation, {}, parent=binding.abstract, parent_name=name)
        return fulfilled_params
