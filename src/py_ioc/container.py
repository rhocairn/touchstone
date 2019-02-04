import inspect
from typing import (  # noqa: F401
    Any,
    Dict,
    Optional,
    Tuple,
)

from py_ioc.bindings import (
    Binding,
    ContextualBinding,
    NEW_EVERY_TIME,
    SINGLETON,
    TAbstract,
    TConcrete,
)


class Container:
    def __init__(self):
        self._bindings = {}  # type: Dict[TAbstract, Binding]
        self._instances = {}  # type: Dict[Binding, Any]
        self._contextual_bindings = {}  # type: Dict[Tuple[Optional[TAbstract], TAbstract, Optional[str]], ContextualBinding]  # noqa: E501
        self.bind_instance(Container, self)

    def bind(self, abstract: TAbstract, concrete: TConcrete, lifetime_strategy=NEW_EVERY_TIME) -> None:
        self._bindings[abstract] = Binding(abstract, concrete, lifetime_strategy)

    def bind_instance(self, abstract: TAbstract, instance: object) -> None:
        self._bindings[abstract] = Binding(abstract, lambda: instance, SINGLETON)

    def bind_contextual(self, *,
                        when: TAbstract,
                        wants: Optional[TAbstract] = None,
                        called: Optional[str] = None,
                        give: TConcrete,
                        lifetime_strategy: str = NEW_EVERY_TIME
                        ) -> None:
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

    def make(self, abstract: TAbstract, init_kwargs=None) -> Any:
        return self._make(abstract, init_kwargs, None, None)

    def _make(self, abstract: TAbstract, init_kwargs, parent: Optional[TAbstract], parent_name: Optional[str]) -> Any:
        if init_kwargs is None:
            init_kwargs = {}

        binding = self._resolve_binding(abstract, parent, parent_name)
        if binding in self._instances:
            return self._instances[binding]

        fulfilled_params = self._resolve_params(binding, init_kwargs)
        instance = binding.make(fulfilled_params)
        if binding.lifetime_strategy == SINGLETON:
            self._instances[binding] = instance
        return instance

    def _resolve_binding(self,
                         abstract: Optional[TAbstract],
                         parent: Optional[TAbstract],
                         name: Optional[str],
                         ) -> Binding:
        if parent is not None:
            binding = self._resolve_contextual_binding(abstract, parent, name)
            if binding:
                return binding

        if abstract in self._bindings:
            return self._bindings[abstract]
        if callable(abstract) and not inspect.isabstract(abstract):
            return Binding(abstract, abstract, NEW_EVERY_TIME)

        raise TypeError("Can't fulfill parameter {}.{}: {}".format(parent, name, abstract))

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

    def _resolve_params(self, binding: Binding, init_kwargs: Dict[str, Any]):
        needed_params = binding.get_concrete_params()
        fulfilled_params = {}
        for name, annotation in needed_params.items():
            if name in init_kwargs:
                fulfilled_params[name] = init_kwargs[name]
            else:
                fulfilled_params[name] = self._make(annotation, {}, parent=binding.abstract, parent_name=name)
        return fulfilled_params
