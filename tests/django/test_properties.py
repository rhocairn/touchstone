from unittest.mock import patch

import pytest
from touchstone import Container
from touchstone.bindings import AnnotationHint
from touchstone.django.properties import MagicProperty, inject_magic_properties


class MyAbc:
    pass


class MyCls(MyAbc):
    pass


class TestInjectMagicProperties:
    def test_inject_magic_properties_uses_get_container(self):
        class Thing:
            obj: MyAbc

        container = Container()
        container.bind(MyAbc, MyCls)
        with patch("touchstone.django.properties.get_container", return_value=container):
            Thing2 = inject_magic_properties(Thing)

            assert Thing2 is Thing
            assert isinstance(Thing.obj, MagicProperty)

            thing = Thing()
            assert isinstance(thing.obj, MyCls)

    def test_inject_magic_properties_properties_are_cached_per_instance(self):
        class Thing:
            obj: MyAbc

        container = Container()
        container.bind(MyAbc, MyCls)
        with patch("touchstone.django.properties.get_container", return_value=container):
            inject_magic_properties(Thing)
            thing = Thing()

            assert isinstance(thing.obj, MyCls)
            thing_obj1 = thing.obj
            thing_obj2 = thing.obj
            assert thing_obj1 is thing_obj2

            thing2 = Thing()
            assert thing2.obj is not thing.obj

    def test_inject_magic_properties_two_injected_properties(self):
        # Regression: There was originally a bug in the handling of closures
        # which leaked data and caused all properties on the same cls to have the same
        # object injected!

        class BigThing:
            obj1: MyAbc
            obj2: MyAbc

        container = Container()
        container.bind(MyAbc, MyCls)
        with patch("touchstone.django.properties.get_container", return_value=container):
            inject_magic_properties(BigThing)
            thing = BigThing()

            assert isinstance(thing.obj1, MyCls)
            assert isinstance(thing.obj2, MyCls)
            assert thing.obj1 is not thing.obj2

    def test_inject_magic_properties_uses_late_retrieval_of_container(self):
        class Thing:
            obj: MyAbc

        inject_magic_properties(Thing)
        thing = Thing()

        with patch("touchstone.django.properties.get_container") as mock_get_container:
            container = Container()
            mock_get_container.return_value = container
            late_bound_obj = MyCls()
            container.bind_contextual(when=Thing, wants=MyAbc, give=lambda: late_bound_obj)

            assert thing.obj is late_bound_obj


class TestMagicProperty:
    @patch("touchstone.django.properties.get_container")
    def test_as_standard_descriptor(self, mock_get_container):
        mock_get_container.return_value = Container()

        class Owner:
            obj = MagicProperty(abstract=MyCls, default_value=AnnotationHint.NO_DEFAULT_VALUE)

        owner_obj = Owner().obj
        assert isinstance(owner_obj, MyCls)

    def test__get__raises_if_not_assigned_name(self):
        class Owner:
            pass

        Owner.prop = MagicProperty(abstract=MyCls, default_value=AnnotationHint.NO_DEFAULT_VALUE)

        with pytest.raises(TypeError, match="has not been assigned a name"):
            Owner().prop

    @patch("touchstone.django.properties.get_container")
    def test__get__uses_container_to_make(self, mock_get_container):
        class Owner:
            pass

        prop = MagicProperty(abstract=MyCls, default_value=AnnotationHint.NO_DEFAULT_VALUE)
        prop.__set_name__(Owner, "prop")
        Owner.prop = prop

        singleton_obj = MyCls()
        container = Container()
        mock_get_container.return_value = container
        container.bind_instance(MyCls, singleton_obj)

        owners_prop = Owner().prop
        assert owners_prop is singleton_obj

    @patch("touchstone.django.properties.get_container")
    def test__get__result_is_cached_per_instance(self, mock_get_container):
        class Owner:
            pass

        prop = MagicProperty(abstract=MyCls, default_value=AnnotationHint.NO_DEFAULT_VALUE)
        prop.__set_name__(Owner, "prop")
        Owner.prop = prop

        mock_get_container.return_value = Container()

        owner = Owner()
        owners_prop_1 = owner.prop
        owners_prop_2 = owner.prop
        assert owners_prop_1 is owners_prop_2

    @patch("touchstone.django.properties.get_container")
    def test__get__result_is_not_cached_per_type(self, mock_get_container):
        class Owner:
            pass

        prop = MagicProperty(abstract=MyCls, default_value=AnnotationHint.NO_DEFAULT_VALUE)
        prop.__set_name__(Owner, "prop")
        Owner.prop = prop

        mock_get_container.return_value = Container()

        owner_1_prop = Owner().prop
        owner_2_prop = Owner().prop
        assert owner_1_prop is not owner_2_prop

    def test__set_name__sets_name(self):
        class Owner:
            pass

        prop = MagicProperty(abstract=MyCls, default_value=AnnotationHint.NO_DEFAULT_VALUE)
        prop.__set_name__(Owner, "myprop")
        assert prop.name == "myprop"

    def test__set_name__calling_twice_with_same_name_is_ok(self):
        class Owner:
            pass

        prop = MagicProperty(abstract=MyCls, default_value=AnnotationHint.NO_DEFAULT_VALUE)
        prop.__set_name__(Owner, "myprop")
        prop.__set_name__(Owner, "myprop")

    def test__set_name__raises_if_name_mismatch(self):
        class Owner:
            pass

        prop = MagicProperty(abstract=MyCls, default_value=AnnotationHint.NO_DEFAULT_VALUE)
        prop.__set_name__(Owner, "myprop")
        with pytest.raises(TypeError, match="two different names"):
            prop.__set_name__(Owner, "otherprop")
