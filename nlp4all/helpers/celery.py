import typing as t
from celery import Celery, Task, shared_task

if t.TYPE_CHECKING:
    from flask import Flask


def celery_init_app(app: 'Flask') -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


@shared_task(ignore_result=False)
def add_test(x: int, y: int) -> int:
    return x + y
