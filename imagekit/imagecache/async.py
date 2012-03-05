# -*- coding: utf-8 -*-
from celery.task import task

from imagekit.imagecache.base import PessimisticImageCacheBackend


@task
def generate(model, pk, attr):
    try:
        instance = model._default_manager.get(pk=pk)
    except model.DoesNotExist:
        pass  # The model was deleted since the task was scheduled. NEVER MIND!
    else:
        getattr(instance, attr).generate(save=True)


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

    def invalidate(self, file):
        generate.delay(file.instance.__class__, file.instance.pk, file.attname)

    def clear(self, file):
        file.delete(save=False)
