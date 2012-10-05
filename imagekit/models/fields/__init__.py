import os

from django.db import models
from .files import ProcessedImageFieldFile
from .utils import ImageSpecFileDescriptor, ImageKitMeta
from ..receivers import configure_receivers
from ...base import ImageSpec
from ...utils import suggest_extension
from ...specs import SpecHost


class ImageSpecField(SpecHost):
    """
    The heart and soul of the ImageKit library, ImageSpecField allows you to add
    variants of uploaded images to your models.

    """
    def __init__(self, processors=None, format=None, options=None,
        image_field=None, storage=None, autoconvert=None,
        image_cache_backend=None, image_cache_strategy=None, spec=None,
        id=None):

        # The spec accepts a callable value for processors, but it
        # takes different arguments than the callable that ImageSpecField
        # expects, so we create a partial application and pass that instead.
        # TODO: Should we change the signatures to match? Even if `instance` is not part of the signature, it's accessible through the source file object's instance property.
        p = lambda file: processors(instance=file.instance,
                file=file) if callable(processors) else processors

        SpecHost.__init__(self, processors=p, format=format,
                options=options, storage=storage, autoconvert=autoconvert,
                image_cache_backend=image_cache_backend,
                image_cache_strategy=image_cache_strategy, spec=spec, id=id)

        self.image_field = image_field

    @property
    def storage(self):
        return self.spec.storage

    def contribute_to_class(self, cls, name):
        setattr(cls, name, ImageSpecFileDescriptor(self, name))
        try:
            # Make sure we don't modify an inherited ImageKitMeta instance
            ik = cls.__dict__['ik']
        except KeyError:
            try:
                base = getattr(cls, '_ik')
            except AttributeError:
                ik = ImageKitMeta()
            else:
                # Inherit all the spec fields.
                ik = ImageKitMeta(base.spec_fields)
            setattr(cls, '_ik', ik)
        ik.spec_fields.append(name)

        # Generate a spec_id to register the spec with. The default spec id is
        # "<app>:<model>_<field>"
        if not self.spec_id:
            self.spec_id = (u'%s:%s_%s' % (cls._meta.app_label,
                    cls._meta.object_name, name)).lower()

        # Register the spec with the id. This allows specs to be overridden
        # later, from outside of the model definition.
        self.register_spec(self.spec_id)

        # Register the field with the image_cache_backend
        try:
            self.spec.image_cache_backend.register_field(cls, self, name)
        except AttributeError:
            pass


class ProcessedImageField(models.ImageField):
    """
    ProcessedImageField is an ImageField that runs processors on the uploaded
    image *before* saving it to storage. This is in contrast to specs, which
    maintain the original. Useful for coercing fileformats or keeping images
    within a reasonable size.

    """
    attr_class = ProcessedImageFieldFile

    def __init__(self, processors=None, format=None, options=None,
        verbose_name=None, name=None, width_field=None, height_field=None,
        autoconvert=True, **kwargs):
        """
        The ProcessedImageField constructor accepts all of the arguments that
        the :class:`django.db.models.ImageField` constructor accepts, as well
        as the ``processors``, ``format``, and ``options`` arguments of
        :class:`imagekit.models.ImageSpecField`.

        """
        models.ImageField.__init__(self, verbose_name, name, width_field,
                height_field, **kwargs)
        self.spec = ImageSpec(processors, format=format, options=options,
                autoconvert=autoconvert)

    def get_filename(self, filename):
        filename = os.path.normpath(self.storage.get_valid_name(
                os.path.basename(filename)))
        name, ext = os.path.splitext(filename)
        ext = suggest_extension(filename, self.spec.format)
        return u'%s%s' % (name, ext)


try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    pass
else:
    add_introspection_rules([], [r'^imagekit\.models\.fields\.ProcessedImageField$'])


configure_receivers()
