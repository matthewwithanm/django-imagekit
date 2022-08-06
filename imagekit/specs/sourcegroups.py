"""
Source groups are the means by which image spec sources are identified. They
have two responsibilities:

1. To dispatch ``source_saved`` signals. (These will be relayed to the
   corresponding specs' cache file strategies.)
2. To provide the source files that they represent, via a generator method named
   ``files()``. (This is used by the generateimages management command for
   "pre-caching" image files.)

"""

import inspect

from django.db.models.signals import post_init, post_save
from django.utils.functional import wraps

from ..cachefiles import LazyImageCacheFile
from ..signals import source_saved
from ..utils import get_nonabstract_descendants


def ik_model_receiver(fn):
    """
    A method decorator that filters out signals coming from models that don't
    have fields that function as ImageFieldSourceGroup sources.

    """
    @wraps(fn)
    def receiver(self, sender, **kwargs):
        if not inspect.isclass(sender):
            return
        for src in self._source_groups:
            if issubclass(sender, src.model_class):
                fn(self, sender=sender, **kwargs)

                # If we find a match, return. We don't want to handle the signal
                # more than once.
                return
    return receiver


class ModelSignalRouter:
    """
    Normally, ``ImageFieldSourceGroup`` would be directly responsible for
    watching for changes on the model field it represents. However, Django does
    not dispatch events for abstract base classes. Therefore, we must listen for
    the signals on all models and filter out those that aren't represented by
    ``ImageFieldSourceGroup``s. This class encapsulates that functionality.

    Related:
        https://github.com/matthewwithanm/django-imagekit/issues/126
        https://code.djangoproject.com/ticket/9318

    """

    def __init__(self):
        self._source_groups = []
        uid = 'ik_spec_field_receivers'
        post_init.connect(self.post_init_receiver, dispatch_uid=uid)
        post_save.connect(self.post_save_receiver, dispatch_uid=uid)

    def add(self, source_group):
        self._source_groups.append(source_group)

    def init_instance(self, instance):
        instance._ik = getattr(instance, '_ik', {})

    def update_source_hashes(self, instance):
        """
        Stores hashes of the source image files so that they can be compared
        later to see whether the source image has changed (and therefore whether
        the spec file needs to be regenerated).

        """
        self.init_instance(instance)
        instance._ik['source_hashes'] = {
            attname: hash(getattr(instance, attname))
            for attname in self.get_source_fields(instance)}
        return instance._ik['source_hashes']

    def get_source_fields(self, instance):
        """
        Returns a list of the source fields for the given instance.

        """
        return {
            src.image_field
            for src in self._source_groups
            if isinstance(instance, src.model_class)}

    @ik_model_receiver
    def post_save_receiver(self, sender, instance=None, created=False, update_fields=None, raw=False, **kwargs):
        if not raw:
            self.init_instance(instance)
            old_hashes = instance._ik.get('source_hashes', {}).copy()
            new_hashes = self.update_source_hashes(instance)
            for attname in self.get_source_fields(instance):
                if update_fields and attname not in update_fields:
                    continue

                file = getattr(instance, attname)
                if file and old_hashes.get(attname) != new_hashes[attname]:
                    self.dispatch_signal(source_saved, file, sender, instance,
                                         attname)

    @ik_model_receiver
    def post_init_receiver(self, sender, instance=None, **kwargs):
        self.init_instance(instance)
        source_fields = self.get_source_fields(instance)
        local_fields = {
            field.name: field
            for field in instance._meta.local_fields
            if field.name in source_fields}
        instance._ik['source_hashes'] = {
            attname: hash(file_field)
            for attname, file_field in local_fields.items()}

    def dispatch_signal(self, signal, file, model_class, instance, attname):
        """
        Dispatch the signal for each of the matching source groups. Note that
        more than one source can have the same model and image_field; it's
        important that we dispatch the signal for each.

        """
        for source_group in self._source_groups:
            if issubclass(model_class, source_group.model_class) and source_group.image_field == attname:
                signal.send(sender=source_group, source=file)


class ImageFieldSourceGroup:
    """
    A source group that represents a particular field across all instances of a
    model and its subclasses.

    """
    def __init__(self, model_class, image_field):
        self.model_class = model_class
        self.image_field = image_field
        signal_router.add(self)

    def files(self):
        """
        A generator that returns the source files that this source group
        represents; in this case, a particular field of every instance of a
        particular model and its subclasses.

        """
        for model in get_nonabstract_descendants(self.model_class):
            for instance in model.objects.all().iterator():
                yield getattr(instance, self.image_field)


class SourceGroupFilesGenerator:
    """
    A Python generator that yields cache file objects for source groups.

    """
    def __init__(self, source_group, generator_id):
        self.source_group = source_group
        self.generator_id = generator_id

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.source_group, self.generator_id))

    def __call__(self):
        for source_file in self.source_group.files():
            yield LazyImageCacheFile(self.generator_id,
                                              source=source_file)


signal_router = ModelSignalRouter()
