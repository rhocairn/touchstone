import inspect

from touchstone.bindings import (
    AbstractBinding,
    AnnotationHint,
    AutoBinding,
    BindingResolver,
    ContextualBinding,
    NEW_EVERY_TIME,
    SINGLETON,
    SimpleBinding,
)


class ClassWithoutDefaults:
    bar: str

    def __init__(self, foo: dict):
        self.foo = foo


class ClassWithDefaults:
    DCT = {}
    bar: str

    def __init__(self, foo: dict = DCT):
        self.foo = foo
        self.bar = 'barista'


class MyBinding(AbstractBinding):
    def __init__(self, cls):
        self.abstract = cls
        self.concrete = cls

    def is_contextual(self):
        return False

    def __hash__(self):
        return 0


class TestAbstractBinding:

    def test_make(self):
        foo = {'foo': 'bar'}
        binding = MyBinding(ClassWithDefaults)
        obj = binding.make({'foo': foo})
        assert isinstance(obj, ClassWithDefaults)
        assert obj.foo is foo

    def test_get_concrete_params(self):
        binding = MyBinding(ClassWithoutDefaults)
        params = binding.get_concrete_params()
        assert set(params.keys()) == {'foo'}
        assert params['foo'].annotation is dict
        assert params['foo'].default_value is AnnotationHint.NO_DEFAULT_VALUE
        assert not params['foo'].has_default_value()

    def test_get_concrete_attributes(self):
        binding = MyBinding(ClassWithoutDefaults)
        instance = ClassWithoutDefaults({})
        attrs = binding.get_concrete_attrs(instance)
        assert set(attrs.keys()) == {'bar'}
        assert attrs['bar'].annotation is str
        assert attrs['bar'].default_value is AnnotationHint.NO_DEFAULT_VALUE
        assert not attrs['bar'].has_default_value()

    def test_get_concrete_params_with_defaults(self):
        binding = MyBinding(ClassWithDefaults)
        params = binding.get_concrete_params()
        assert set(params.keys()) == {'foo'}
        assert params['foo'].annotation is dict
        assert params['foo'].default_value is ClassWithDefaults.DCT
        assert params['foo'].has_default_value()

    def test_get_concrete_attributes_with_defaults(self):
        binding = MyBinding(ClassWithDefaults)
        instance = ClassWithDefaults()
        attrs = binding.get_concrete_attrs(instance)
        assert set(attrs.keys()) == {'bar'}
        assert attrs['bar'].annotation is str
        assert attrs['bar'].default_value == 'barista'
        assert attrs['bar'].has_default_value()


class TestBindingResolver:
    def test_auto_binding(self):
        class MyCls:
            pass

        bindings = BindingResolver()
        binding = bindings.resolve_binding(MyCls)

        assert isinstance(binding, AutoBinding)
        assert binding.abstract is MyCls
        assert binding.concrete is MyCls
        assert binding.lifetime_strategy == NEW_EVERY_TIME

    def test_simple_binding(self):
        class MyAbc:
            pass

        class MyCls(MyAbc):
            pass

        bindings = BindingResolver()
        bindings.bind(MyAbc, MyCls)

        binding = bindings.resolve_binding(MyAbc)

        assert isinstance(binding, SimpleBinding)
        assert binding.abstract is MyAbc
        assert binding.concrete is MyCls
        assert binding.lifetime_strategy == NEW_EVERY_TIME

    def test_simple_binding_singleton(self):
        class MyAbc:
            pass

        class MyCls(MyAbc):
            pass

        bindings = BindingResolver()
        bindings.bind(MyAbc, MyCls, SINGLETON)

        binding = bindings.resolve_binding(MyAbc)

        assert isinstance(binding, SimpleBinding)
        assert binding.abstract is MyAbc
        assert binding.concrete is MyCls
        assert binding.lifetime_strategy == SINGLETON

    def test_contextual_binding_full(self):
        class MyAbc:
            pass

        class MyCls(MyAbc):
            pass

        class Thing:
            def __init__(self, obj: MyAbc):
                self.obj = obj

        bindings = BindingResolver()
        bindings.bind_contextual(when=Thing, wants=MyAbc, called='obj', give=MyCls)

        binding = bindings.resolve_binding(MyAbc, parent=Thing, name='obj')

        assert isinstance(binding, ContextualBinding)
        assert binding.abstract is MyAbc
        assert binding.concrete is MyCls
        assert binding.parent is Thing
        assert binding.parent_name == 'obj'
        assert binding.lifetime_strategy == NEW_EVERY_TIME

    def test_contextual_binding_just_cls(self):
        class MyAbc:
            pass

        class MyCls(MyAbc):
            pass

        class Thing:
            def __init__(self, obj: MyAbc):
                self.obj = obj

        bindings = BindingResolver()
        bindings.bind_contextual(when=Thing, wants=MyAbc, give=MyCls)

        binding = bindings.resolve_binding(MyAbc, parent=Thing, name='obj')

        assert isinstance(binding, ContextualBinding)
        assert binding.abstract is MyAbc
        assert binding.concrete is MyCls
        assert binding.parent is Thing
        assert binding.parent_name is None
        assert binding.lifetime_strategy == NEW_EVERY_TIME

    def test_contextual_binding_just_name(self):
        class MyAbc:
            pass

        class MyCls(MyAbc):
            pass

        class Thing:
            def __init__(self, obj):
                self.obj = obj

        bindings = BindingResolver()
        bindings.bind_contextual(when=Thing, called='obj', give=MyCls)

        binding = bindings.resolve_binding(abstract=inspect.Parameter.empty, parent=Thing, name='obj')

        assert isinstance(binding, ContextualBinding)
        assert binding.abstract is None
        assert binding.concrete is MyCls
        assert binding.parent is Thing
        assert binding.parent_name == 'obj'
        assert binding.lifetime_strategy == NEW_EVERY_TIME

    def test_contextual_binding_singleton(self):
        class MyAbc:
            pass

        class MyCls(MyAbc):
            pass

        class Thing:
            def __init__(self, obj: MyAbc):
                self.obj = obj

        bindings = BindingResolver()
        bindings.bind_contextual(when=Thing, wants=MyAbc, called='obj', give=MyCls, lifetime_strategy=SINGLETON)

        binding = bindings.resolve_binding(MyAbc, parent=Thing, name='obj')

        assert isinstance(binding, ContextualBinding)
        assert binding.abstract is MyAbc
        assert binding.concrete is MyCls
        assert binding.parent is Thing
        assert binding.parent_name == 'obj'
        assert binding.lifetime_strategy == SINGLETON


    def test_default_value_binding(self):
        class Thing:
            def __init__(self, obj: str = 'asd'):
                self.obj = obj

        bindings = BindingResolver()
        binding = bindings.resolve_binding(str, parent=Thing, name='obj', default_value='asd')

        assert isinstance(binding, ContextualBinding)
        assert binding.abstract is str
        assert binding.concrete() == 'asd'
        assert binding.parent is Thing
        assert binding.parent_name == 'obj'
        assert binding.lifetime_strategy == NEW_EVERY_TIME
