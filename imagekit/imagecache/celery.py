# -*- coding: utf-8 -*-
from __future__ import absolute_import

from imagekit.imagecache import PessimisticImageCacheBackend, InvalidImageCacheBackendError


def generate(model, pk, attr):
    try:
        instance = model._default_manager.get(pk=pk)
    except model.DoesNotExist:
        pass  # The model was deleted since the task was scheduled. NEVER MIND!
    else:
        field_file = getattr(instance, attr)
        field_file.delete(save=False)
        field_file.generate(save=True)


class CeleryImageCacheBackend(PessimisticImageCacheBackend):
    """
    A pessimistic cache state backend that uses celery to generate its spec
    images. Like PessimisticCacheStateBackend, this one checks to see if the
    file exists on validation, so the storage is hit fairly frequently, but an
    image is guaranteed to exist. However, while validation guarantees the
    existence of *an* image, it does not necessarily guarantee that you will get
    the correct image, as the spec may be pending regeneration. In other words,
    while there are `generate` tasks in the queue, it is possible to get a
    stale spec image. The tradeoff is that calling `invalidate()` won't block
    to interact with file storage.

    """
    def __init__(self):
        try:
            from celery.task import task
        except:
            raise InvalidImageCacheBackendError("Celery image cache backend requires the 'celery' library")
        if not getattr(CeleryImageCacheBackend, '_task', None):
            CeleryImageCacheBackend._task = task(generate)

    def invalidate(self, file):
        self._task.delay(file.instance.__class__, file.instance.pk, file.attname)

    def clear(self, file):
        file.delete(save=False)
