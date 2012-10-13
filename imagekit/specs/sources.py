from django.db.models.signals import post_init, post_save, post_delete
from django.utils.functional import wraps
from .signals import source_created, source_changed, source_deleted


def ik_model_receiver(fn):
    """
    A method decorator that filters out signals coming from models that don't
    have fields that function as ImageFieldSpecSources

    """
    @wraps(fn)
    def receiver(self, sender, **kwargs):
        if sender in (src.model_class for src in self._sources):
            fn(self, sender=sender, **kwargs)
    return receiver


class ModelSignalRouter(object):
    """
    Handles signals dispatched by models and relays them to the spec sources
    that represent those models.

    """

    def __init__(self):
        self._sources = []
        uid = 'ik_spec_field_receivers'
        post_init.connect(self.post_init_receiver, dispatch_uid=uid)
        post_save.connect(self.post_save_receiver, dispatch_uid=uid)
        post_delete.connect(self.post_delete_receiver, dispatch_uid=uid)

    def add(self, source):
        self._sources.append(source)

    def init_instance(self, instance):
        instance._ik = getattr(instance, '_ik', {})

    def update_source_hashes(self, instance):
        """
        Stores hashes of the source image files so that they can be compared
        later to see whether the source image has changed (and therefore whether
        the spec file needs to be regenerated).

        """
        self.init_instance(instance)
        instance._ik['source_hashes'] = dict((attname, hash(file_field))
                for attname, file_field in self.get_field_dict(instance).items())
        return instance._ik['source_hashes']

    def get_field_dict(self, instance):
        """
        Returns the source fields for the given instance, in a dictionary whose
        keys are the field names and values are the fields themselves.

        """
        return dict((src.image_field, getattr(instance, src.image_field)) for
                src in self._sources if src.model_class is instance.__class__)

    @ik_model_receiver
    def post_save_receiver(self, sender, instance=None, created=False, raw=False, **kwargs):
        if not raw:
            self.init_instance(instance)
            old_hashes = instance._ik.get('source_hashes', {}).copy()
            new_hashes = self.update_source_hashes(instance)
            for attname, file in self.get_field_dict(instance).items():
                if created:
                    self.dispatch_signal(source_created, file, sender)
                elif old_hashes[attname] != new_hashes[attname]:
                    self.dispatch_signal(source_changed, file, sender)

    @ik_model_receiver
    def post_delete_receiver(self, sender, instance=None, **kwargs):
        for attname, file in self.get_field_dict(instance):
            self.dispatch_signal(source_deleted, file, sender)

    @ik_model_receiver
    def post_init_receiver(self, sender, instance=None, **kwargs):
        self.update_source_hashes(instance)

    def dispatch_signal(self, signal, file, model_class):
        """
        Dispatch the signal for each of the matching sources. Note that more
        than one source can have the same model and image_field; it's important
        that we dispatch the signal for each.

        """
        for source in self._sources:
            # TODO: Is it okay to require a field attribute on our file?
            if source.model_class is model_class and source.image_field == file.field.attname:
                signal.send(sender=source, source_file=file)


class ImageFieldSpecSource(object):
    def __init__(self, model_class, image_field):
        """
        Good design would dictate that this instance would be responsible for
        watching for changes for the provided field. However, due to a bug in
        Django, we can't do that without leaving abstract base models (which
        don't trigger signals) in the lurch. So instead, we do all signal
        handling through the signal router.

        Related:
            https://github.com/jdriscoll/django-imagekit/issues/126
            https://code.djangoproject.com/ticket/9318

        """
        self.model_class = model_class
        self.image_field = image_field
        signal_router.add(self)


signal_router = ModelSignalRouter()
