# -*- coding: utf-8 -*-
from __future__ import absolute_import

from .base import InvalidImageCacheBackendError, Simple as SimpleBackend


def generate(model, pk, attr):
    try:
        instance = model._default_manager.get(pk=pk)
    except model.DoesNotExist:
        pass  # The model was deleted since the task was scheduled. NEVER MIND!
    else:
        field_file = getattr(instance, attr)
        field_file.delete(save=False)
        field_file.generate(save=True)


class CeleryBackend(SimpleBackend):
    """
    An image cache backend that uses celery to generate images.

    """
    def __init__(self):
        try:
            from celery.task import task
        except:
            raise InvalidImageCacheBackendError("Celery validation backend requires the 'celery' library")
        if not getattr(CeleryBackend, '_task', None):
            CeleryBackend._task = task(generate)

    def invalidate(self, file):
        self._task.delay(file.instance.__class__, file.instance.pk, file.attname)

    def clear(self, file):
        file.delete(save=False)
