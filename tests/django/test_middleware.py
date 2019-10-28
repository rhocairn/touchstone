from unittest import mock
from unittest.mock import MagicMock

from django.views import View

from touchstone.django import InjectViewsMiddleware


class MyAbc:
    pass


class MyCls(MyAbc):
    pass


class MyView(View):
    obj: MyAbc

    def get(self):
        return self.obj


class TestInjectViewsMiddleware:
    def test_process_view(self):
        view_func = MyView.as_view()
        with mock.patch(
            "touchstone.django.middleware.inject_magic_properties"
        ) as mock_inject_magic_properties:
            middleware = InjectViewsMiddleware(MagicMock())
            request = None
            middleware.process_view(request, view_func, [], {})

        mock_inject_magic_properties.assert_called_once_with(MyView)
