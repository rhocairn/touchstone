from django.utils.functional import cached_property

from touchstone import Container
from touchstone.django import MagicInjectedProperties


class MyAbc:
    pass

class MyCls(MyAbc):
    pass


class TestMagicInjectedProperties:
    def test_set_magic_properties(self):
        class Thing:
            obj: MyAbc

        container = Container()
        container.bind(MyAbc, MyCls)
        magic = MagicInjectedProperties(container)
        Thing2 = magic.set_magic_properties(Thing)

        assert Thing2 is Thing
        assert isinstance(Thing.obj, cached_property)

        thing = Thing()
        assert isinstance(thing.obj, MyCls)

    def test_set_magic_properties_properties_are_cached_per_instance(self):
        class Thing:
            obj: MyAbc

        container = Container()
        container.bind(MyAbc, MyCls)
        magic = MagicInjectedProperties(container)
        magic.set_magic_properties(Thing)

        thing = Thing()
        assert isinstance(thing.obj, MyCls)
        thing_obj1 = thing.obj
        thing_obj2 = thing.obj
        assert thing_obj1 is thing_obj2

        thing2 = Thing()
        assert thing2.obj is not thing.obj

    def test_set_magic_properties_two_injected_properties(self):
        # Regression: There was originally a bug in the handling of closures
        # which leaked data and caused all properties on the same cls to have the same
        # object injected!

        class BigThing:
            obj1: MyAbc
            obj2: MyAbc

        container = Container()
        container.bind(MyAbc, MyCls)
        magic = MagicInjectedProperties(container)
        magic.set_magic_properties(BigThing)

        thing = BigThing()
        assert isinstance(thing.obj1, MyCls)
        assert isinstance(thing.obj2, MyCls)
        assert thing.obj1 is not thing.obj2
