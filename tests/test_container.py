import abc

import pytest

from py_ioc.container import (
    Container,
    SINGLETON,
)


class TestContainer:
    def test_make_simple_autowiring_with_concrete_annotations(self):
        class X:
            pass

        class Y:
            def __init__(self, x: X):
                self.x = x

        container = Container()
        y = container.make(Y)
        assert isinstance(y, Y)
        assert isinstance(y.x, X)

    def test_make_simple_autowiring_with_abstract_annotations(self):
        class X:
            pass

        class XX(X):
            pass

        class Y:
            def __init__(self, x: X):
                self.x = x

        container = Container()
        container.bind(X, XX)
        y = container.make(Y)
        assert isinstance(y, Y)
        assert isinstance(y.x, X)
        assert isinstance(y.x, XX)

    def test_make_simple_autowiring_with_factory_method_annotations(self):
        class X:
            pass

        class Y:
            def __init__(self, x: X):
                self.x = x

        def make_x():
            x = X()
            x.foo = 'bar'
            return x

        container = Container()
        container.bind(X, make_x)
        y = container.make(Y)
        assert isinstance(y, Y)
        assert isinstance(y.x, X)
        assert y.x.foo == 'bar'

    def test_make_raises_if_not_concrete(self):
        class X(abc.ABC):
            @abc.abstractmethod
            def foo(self):
                pass

        container = Container()
        with pytest.raises(TypeError):
            container.make(X)

    def test_make_string_argument_works(self):
        def make_n():
            return 5

        container = Container()
        container.bind('n', make_n)
        assert container.make('n') == 5

    def test_make_string_argument_in_subrequirement(self):
        class X:
            def __init__(self, arg: 'n'):  # type: ignore  # noqa: F821
                self.arg = arg

        def make_n():
            return 5

        container = Container()
        container.bind('n', make_n)
        assert container.make(X).arg == 5

    def test_make_is_not_caching(self):
        class X:
            pass

        container = Container()
        x1 = container.make(X)
        x2 = container.make(X)
        assert x1 is not x2

    def test_make_passes_kwargs(self):
        class X:
            def __init__(self, foo):
                self.foo = foo

        container = Container()
        x = container.make(X, {'foo': 'bar'})
        assert x.foo == 'bar'

    def test_make_with_singletons(self):
        class X:
            pass

        container = Container()
        container.bind(X, X, lifetime_strategy=SINGLETON)
        x1 = container.make(X)
        x2 = container.make(X)
        assert x1 is x2

    def test_make_will_inject_container(self):
        def returns_arg(c: Container):
            return c

        container = Container()
        arg = container.make(returns_arg)
        assert arg is container

    # requires python >= 3.6
    # def test_make_injects_class_annotations(self):
    #     class X:
    # pass
    #
    #     class Y:
    #         foo: X
    #
    #     container = Container()
    #     y = container.make(Y)
    #     assert isinstance(y.foo, X)

    def test_make_supports_contextual_binding(self):
        class X:
            def __init__(self, foo):
                self.foo = foo

        class Y1:
            def __init__(self, x: X):
                self.x = x

        class Y2:
            def __init__(self, x: X):
                self.x = x

        container = Container()
        container.bind_contextual(when=Y1, wants=X, give=lambda: X('bar1'))
        container.bind_contextual(when=Y2, wants=X, give=lambda: X('bar2'))

        y1 = container.make(Y1)
        y2 = container.make(Y2)
        assert y1.x.foo == 'bar1'
        assert y2.x.foo == 'bar2'

    def test_make_supports_contextual_binding_with_varnae(self):
        class X:
            def __init__(self, foo):
                self.foo = foo

        class Y:
            def __init__(self, x1: X, x2: X):
                self.x1 = x1
                self.x2 = x2

        container = Container()
        container.bind_contextual(when=Y, wants=X, called='x1', give=lambda: X('bar1'))
        container.bind_contextual(when=Y, wants=X, called='x2', give=lambda: X('bar2'))

        y = container.make(Y)
        assert y.x1.foo == 'bar1'
        assert y.x2.foo == 'bar2'

    def test_make_supports_contextual_binding_with_only_varnae(self):
        class X:
            def __init__(self, foo):
                self.foo = foo

        class Y:
            def __init__(self, x1, x2):
                self.x1 = x1
                self.x2 = x2

        container = Container()
        container.bind_contextual(when=Y, called='x1', give=lambda: X('bar1'))
        container.bind_contextual(when=Y, called='x2', give=lambda: X('bar2'))

        y = container.make(Y)
        assert y.x1.foo == 'bar1'
        assert y.x2.foo == 'bar2'

    @pytest.mark.parametrize('typ', [str, bytes, int, float, complex, dict, tuple, list])
    def test_make_does_not_create_primitive_types(self, typ):
        container = Container()
        with pytest.raises(TypeError):
            container.make(typ)

    def test_make_does_not_create_primitive_types_2(self):
        class X:
            def __init__(self, foo: str):
                self.foo = foo

        container = Container()
        with pytest.raises(TypeError):
            container.make(X)

    def test_make_does_not_support_varname_only_binding_if_annotations_used(self):
        class X:
            def __init__(self, foo: str):
                self.foo = foo

        class Y:
            def __init__(self, x1: X, x2: X):
                self.x1 = x1
                self.x2 = x2

        container = Container()
        container.bind_contextual(when=Y, called='x1', give=lambda: X('foo'))
        container.bind_contextual(when=Y, called='x2', give=lambda: X('bar'))

        with pytest.raises(TypeError):
            container.make(Y)

    def test_bind_contextual_needs_either_varname_or_needs_arg(self):
        container = Container()
        with pytest.raises(TypeError):
            container.bind_contextual(when=object, give=object)

    def test_contextual_bindings_does_not_override_global_singleton(self):
        class X:
            pass

        class Y:
            def __init__(self, x: X):
                self.x = x

        container = Container()
        container.bind(X, X, SINGLETON)
        container.bind_contextual(when=Y, wants=X, give=X)

        x1 = container.make(X)
        x2 = container.make(X)
        assert x1 is x2

        y = container.make(Y)
        assert y.x is not x1
        assert isinstance(y.x, X)

    def test_contextual_bindings_singleton(self):
        class X:
            pass

        class Y:
            def __init__(self, x: X):
                self.x = x

        container = Container()
        container.bind_contextual(when=Y, wants=X, give=X, lifetime_strategy=SINGLETON)

        x1 = container.make(X)
        x2 = container.make(X)
        assert x1 is not x2

        y1 = container.make(Y)
        y2 = container.make(Y)
        assert y1.x is not x1
        assert y1.x is y2.x
