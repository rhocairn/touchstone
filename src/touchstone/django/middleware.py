from typing import Any, Callable, Mapping, Sequence

from django.http import HttpRequest, HttpResponse

from touchstone.django.properties import MagicInjectedProperties, get_container


class InjectViewsMiddleware:
    def __init__(self, get_response: Callable) -> None:
        self.magic = MagicInjectedProperties(get_container())
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_view(
        self,
        request: HttpRequest,
        view_func: Any,
        view_args: Sequence[Any],
        view_kwargs: Mapping[str, Any],
    ) -> None:
        if not hasattr(view_func, "view_class"):
            return

        self.magic.set_magic_properties(view_func.view_class)
