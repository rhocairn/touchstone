from unittest import mock
from unittest.mock import MagicMock

from django.views import View
from rest_framework.viewsets import ViewSet
from touchstone.django import InjectViewsMiddleware


class MyAbc:
    pass


class MyCls(MyAbc):
    pass


class DjangoView(View):
    obj: MyAbc

    def get(self):
        return self.obj


class DRFViewSet(ViewSet):
    obj: MyAbc

    def retrieve(self):
        return self.obj


class TestInjectViewsMiddleware:
    def test_process_view_django_style(self):
        view_func = DjangoView.as_view()
        with mock.patch(
            "touchstone.django.middleware.inject_magic_properties"
        ) as mock_inject_magic_properties:
            middleware = InjectViewsMiddleware(MagicMock())
            request = None
            middleware.process_view(request, view_func, [], {})

        mock_inject_magic_properties.assert_called_once_with(DjangoView)

    def test_process_view_drf_style(self):
        view_func = DRFViewSet.as_view({"get": "retrieve"})

        with mock.patch(
            "touchstone.django.middleware.inject_magic_properties"
        ) as mock_inject_magic_properties:
            middleware = InjectViewsMiddleware(MagicMock())
            request = None
            middleware.process_view(request, view_func, [], {})

        mock_inject_magic_properties.assert_called_once_with(DRFViewSet)
