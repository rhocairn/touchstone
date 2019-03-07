from touchstone.bindings import (
    AbstractBinding,
    AnnotationHint,
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
