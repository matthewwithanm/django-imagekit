from django.db import models
from .files import ProcessedImageFieldFile
from .utils import ImageSpecFileDescriptor
from ... import specs
from ...specs import SpecHost
from ...specs.sources import ImageFieldSpecSource


class SpecHostField(SpecHost):
    def set_spec_id(self, cls, name):
        # Generate a spec_id to register the spec with. The default spec id is
        # "<app>:<model>_<field>"
        if not getattr(self, 'spec_id', None):
            spec_id = (u'%s:%s_%s' % (cls._meta.app_label,
                            cls._meta.object_name, name)).lower()

            # Register the spec with the id. This allows specs to be overridden
            # later, from outside of the model definition.
            super(SpecHostField, self).set_spec_id(spec_id)


class ImageSpecField(SpecHostField):
    """
    The heart and soul of the ImageKit library, ImageSpecField allows you to add
    variants of uploaded images to your models.

    """
    def __init__(self, processors=None, format=None, options=None,
        image_field=None, storage=None, autoconvert=None,
        image_cache_backend=None, image_cache_strategy=None, spec=None,
        id=None):

        SpecHost.__init__(self, processors=processors, format=format,
                options=options, storage=storage, autoconvert=autoconvert,
                image_cache_backend=image_cache_backend,
                image_cache_strategy=image_cache_strategy, spec=spec,
                spec_id=id)

        self.image_field = image_field

    @property
    def storage(self):
        return self.spec.storage

    def contribute_to_class(self, cls, name):
        setattr(cls, name, ImageSpecFileDescriptor(self, name))
        self.set_spec_id(cls, name)

        # Add the model and field as a source for this spec id
        specs.registry.add_source(ImageFieldSpecSource(cls, self.image_field),
                                 self.spec_id)


class ProcessedImageField(models.ImageField, SpecHostField):
    """
    ProcessedImageField is an ImageField that runs processors on the uploaded
    image *before* saving it to storage. This is in contrast to specs, which
    maintain the original. Useful for coercing fileformats or keeping images
    within a reasonable size.

    """
    attr_class = ProcessedImageFieldFile

    def __init__(self, processors=None, format=None, options=None,
        verbose_name=None, name=None, width_field=None, height_field=None,
        autoconvert=True, spec=None, spec_id=None, **kwargs):
        """
        The ProcessedImageField constructor accepts all of the arguments that
        the :class:`django.db.models.ImageField` constructor accepts, as well
        as the ``processors``, ``format``, and ``options`` arguments of
        :class:`imagekit.models.ImageSpecField`.

        """
        SpecHost.__init__(self, processors=processors, format=format,
                options=options, autoconvert=autoconvert, spec=spec,
                spec_id=spec_id)
        models.ImageField.__init__(self, verbose_name, name, width_field,
                height_field, **kwargs)

    def contribute_to_class(self, cls, name):
        self.set_spec_id(cls, name)
        return super(ProcessedImageField, self).contribute_to_class(cls, name)


try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    pass
else:
    add_introspection_rules([], [r'^imagekit\.models\.fields\.ProcessedImageField$'])
