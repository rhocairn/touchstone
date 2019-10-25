from typing import Type

import celery
from celery import Celery

from touchstone.django import (
    get_container,
    MagicInjectedProperties,
)


def touchstone_task(cls) -> Type[celery.Task]:
    container = get_container()
    celery_app = container.make(Celery)

    class Task(cls, celery.Task):
        def run(self, *args, **kwargs):
            super(Task, self).run(*args, **kwargs)

    Task = MagicInjectedProperties(container).set_magic_properties(Task)
    return celery_app.register_task(Task())
