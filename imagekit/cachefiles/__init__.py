from django.conf import settings
from django.core.files.images import ImageFile
from django.utils.functional import LazyObject
from ..files import BaseIKFile
from ..registry import generator_registry
from ..signals import before_access
from ..utils import get_logger, get_singleton, generate, get_by_qname


class GeneratedImageFile(BaseIKFile, ImageFile):
    """
    A file that represents the result of a generator. Creating an instance of
    this class is not enough to trigger the generation of the file. In fact,
    one of the main points of this class is to allow the creation of the file
    to be deferred until the time that the cache file strategy requires it.

    """
    def __init__(self, generator, name=None, storage=None, cachefile_backend=None):
        """
        :param generator: The object responsible for generating a new image.
        :param name: The filename
        :param storage: A Django storage object that will be used to save the
            file.
        :param cachefile_backend: The object responsible for managing the
            state of the file.

        """
        self.generator = generator

        name = name or getattr(generator, 'cachefile_name', None)
        if not name:
            fn = get_by_qname(settings.IMAGEKIT_CACHEFILE_NAMER, 'namer')
            name = fn(generator)
        self.name = name

        storage = storage or getattr(generator, 'cachefile_storage',
            None) or get_singleton(settings.IMAGEKIT_DEFAULT_FILE_STORAGE,
            'file storage backend')
        self.cachefile_backend = cachefile_backend or getattr(generator,
            'cachefile_backend', None)

        super(GeneratedImageFile, self).__init__(storage=storage)

    def _require_file(self):
        before_access.send(sender=self, file=self)
        return super(GeneratedImageFile, self)._require_file()

    def generate(self, force=False):
        if force:
            self._generate()
        else:
            self.cachefile_backend.ensure_exists(self)

    def _generate(self):
        # Generate the file
        content = generate(self.generator)

        actual_name = self.storage.save(self.name, content)

        if actual_name != self.name:
            get_logger().warning('The storage backend %s did not save the file'
                    ' with the requested name ("%s") and instead used'
                    ' "%s". This may be because a file already existed with'
                    ' the requested name. If so, you may have meant to call'
                    ' ensure_exists() instead of generate(), or there may be a'
                    ' race condition in the file backend %s. The saved file'
                    ' will not be used.' % (self.storage,
                    self.name, actual_name,
                    self.cachefile_backend))


class LazyGeneratedImageFile(LazyObject):
    def __init__(self, generator_id, *args, **kwargs):
        super(LazyGeneratedImageFile, self).__init__()

        def setup():
            generator = generator_registry.get(generator_id, *args, **kwargs)
            self._wrapped = GeneratedImageFile(generator)

        self.__dict__['_setup'] = setup

    def __repr__(self):
        if self._wrapped is None:
            self._setup()
        return '<%s: %s>' % (self.__class__.__name__, self or 'None')

    def __str__(self):
        if self._wrapped is None:
            self._setup()
        return str(self._wrapped)

    def __unicode__(self):
        if self._wrapped is None:
            self._setup()
        return unicode(self._wrapped)
