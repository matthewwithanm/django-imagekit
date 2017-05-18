from __future__ import unicode_literals

from django.conf import settings
from django.db import models
from django.db.models.signals import class_prepared
from .files import ProcessedImageFieldFile
from .utils import ImageSpecFileDescriptor
from ...specs import SpecHost
from ...specs.sourcegroups import ImageFieldSourceGroup
from ...registry import register


class SpecHostField(SpecHost):
    def _set_spec_id(self, cls, name):
        spec_id = getattr(self, 'spec_id', None)

        # Generate a spec_id to register the spec with. The default spec id is
        # "<app>:<model>_<field>"
        if not spec_id:
            spec_id = ('%s:%s:%s' % (cls._meta.app_label,
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
            source=None, cachefile_storage=None, autoconvert=None,
            cachefile_backend=None, cachefile_strategy=None, spec=None,
            id=None):

        SpecHost.__init__(self, processors=processors, format=format,
                options=options, cachefile_storage=cachefile_storage,
                autoconvert=autoconvert,
                cachefile_backend=cachefile_backend,
                cachefile_strategy=cachefile_strategy, spec=spec,
                spec_id=id)

        # TODO: Allow callable for source. See https://github.com/matthewwithanm/django-imagekit/issues/158#issuecomment-10921664
        self.source = source

    def contribute_to_class(self, cls, name):
        # If the source field name isn't defined, figure it out.

        def register_source_group(source):
            setattr(cls, name, ImageSpecFileDescriptor(self, name, source))
            self._set_spec_id(cls, name)

            # Add the model and field as a source for this spec id
            register.source_group(self.spec_id, ImageFieldSourceGroup(cls, source))

        if self.source:
            register_source_group(self.source)
        else:
            # The source argument is not defined
            # Then we need to see if there is only one ImageField in that model
            # But we need to do that after full model initialization
            def handle_model_preparation(sender, **kwargs):

                image_fields = [f.attname for f in cls._meta.fields if
                                isinstance(f, models.ImageField)]
                if len(image_fields) == 0:
                    raise Exception(
                        '%s does not define any ImageFields, so your %s'
                        ' ImageSpecField has no image to act on.' %
                        (cls.__name__, name))
                elif len(image_fields) > 1:
                    raise Exception(
                        '%s defines multiple ImageFields, but you have not'
                        ' specified a source for your %s ImageSpecField.' %
                        (cls.__name__, name))
                register_source_group(image_fields[0])

            class_prepared.connect(handle_model_preparation, sender=cls, weak=False)


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
            autoconvert=None, spec=None, spec_id=None, **kwargs):
        """
        The ProcessedImageField constructor accepts all of the arguments that
        the :class:`django.db.models.ImageField` constructor accepts, as well
        as the ``processors``, ``format``, and ``options`` arguments of
        :class:`imagekit.models.ImageSpecField`.

        """
        # if spec is not provided then autoconvert will be True by default
        if spec is None and autoconvert is None:
            autoconvert = True

        SpecHost.__init__(self, processors=processors, format=format,
                options=options, autoconvert=autoconvert, spec=spec,
                spec_id=spec_id)
        models.ImageField.__init__(self, verbose_name, name, width_field,
                height_field, **kwargs)

    def contribute_to_class(self, cls, name):
        self._set_spec_id(cls, name)
        return super(ProcessedImageField, self).contribute_to_class(cls, name)


# If the project does not use south, then we will not try to add introspection
if 'south' in settings.INSTALLED_APPS:
    try:
        from south.modelsinspector import add_introspection_rules
    except ImportError:
        pass
    else:
        add_introspection_rules([], [r'^imagekit\.models\.fields\.ProcessedImageField$'])
