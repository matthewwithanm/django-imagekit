from imagekit.utils import get_spec_files


class SignalHandler(object):
    def __init__(self, callback=None):
        if callback is None:
            callback = self.default
        self.callback = callback

    def specs_files(self, instance):
        return get_spec_files(instance)

    def __call__(self, sender, instance=None, **kwargs):
        raise NotImplementedError


class PostSaveHandler(SignalHandler):
    def __call__(self, sender, instance=None, created=False, raw=False, **kwargs):
        if raw:
            return
        for spec in self.specs_files:
            changed = getattr(instance, "_%s_state" % spec.image_field.name) != getattr(instance, spec.image_field.name)
            self.callback(instance, spec, created, changed)

    def default(self, instance=None, spec=None, created=False, changed=False):
        if not created:
            spec.delete(save=False)
        if spec.field.pre_cache:
            spec.generate(False)


class PostDeleteHandler(SignalHandler):
    def __call__(self, sender, instance=None, **kwargs):
        assert instance._get_pk_val() is not None, "%s object can't be deleted because its %s attribute is set to None." % (instance._meta.object_name, instance._meta.pk.attname)
        for spec in self.specs_files:
            self.callback(instance, spec)

    def default(self, instance=None, spec=None):
        spec.delete(save=False)


class PostInitHandler(SignalHandler):
    def __init__(self, image_field):
        self.image_field = image_field

    def __call__(self, sender, instance, **kwargs):
        value = getattr(instance, self.image_field.name)
        setattr(instance, "_%s_state" % self.image_field.name, value)
