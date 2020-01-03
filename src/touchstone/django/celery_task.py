from typing import Any, Type

import celery
from celery import Celery
from touchstone.django import get_container, inject_magic_properties


def touchstone_task(task_cls: type) -> Type[celery.Task]:
    container = get_container()
    celery_app = container.make(Celery)

    class _Task(task_cls, celery.Task):  # type: ignore
        def run(self, *args: Any, **kwargs: Any) -> Any:
            super().run(*args, **kwargs)

    Task = inject_magic_properties(_Task)
    RegisteredTask: Type[celery.Task] = celery_app.register_task(Task())
    return RegisteredTask
