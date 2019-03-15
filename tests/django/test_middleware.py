from unittest import mock
from unittest.mock import MagicMock

from django.views import View

from touchstone import Container
from touchstone.django import InjectViewsMiddleware


class MyAbc:
    pass


class MyCls(MyAbc):
    pass


class MyView(View):
    obj: MyAbc

    def get(self):
        return self.obj


container = Container()
container.bind(MyAbc, MyCls)


class TestInjectViewsMiddleware:
    def test_process_view(self):
        view_func = MyView.as_view()
        with mock.patch('touchstone.django.middleware.get_container', return_value=container):
            with mock.patch('touchstone.django.middleware.MagicInjectedProperties') as mock_MagicInjectedProperties:
                middleware = InjectViewsMiddleware(MagicMock())
                request = None
                middleware.process_view(request, view_func, [], {})

        mock_MagicInjectedProperties.assert_called_once_with(container)
        magic = mock_MagicInjectedProperties.return_value
        magic.set_magic_properties.assert_called_once_with(MyView)
