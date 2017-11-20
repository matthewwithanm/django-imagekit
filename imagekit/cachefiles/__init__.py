from copy import copy
from django.conf import settings
from django.core.files import File
from django.core.files.images import ImageFile
from django.utils.functional import SimpleLazyObject
from django.utils.encoding import smart_str
from ..files import BaseIKFile
from ..registry import generator_registry
from ..signals import content_required, existence_required
from ..utils import get_logger, get_singleton, generate, get_by_qname


class ImageCacheFile(BaseIKFile, ImageFile):
    """
    A file that represents the result of a generator. Creating an instance of
    this class is not enough to trigger the generation of the file. In fact,
    one of the main points of this class is to allow the creation of the file
    to be deferred until the time that the cache file strategy requires it.

    """
    def __init__(self, generator, name=None, storage=None, cachefile_backend=None, cachefile_strategy=None):
        """
        :param generator: The object responsible for generating a new image.
        :param name: The filename
        :param storage: A Django storage object that will be used to save the
            file.
        :param cachefile_backend: The object responsible for managing the
            state of the file.
        :param cachefile_strategy: The object responsible for handling events
            for this file.

        """
        self.generator = generator

        if not name:
            try:
                name = generator.cachefile_name
            except AttributeError:
                fn = get_by_qname(settings.IMAGEKIT_CACHEFILE_NAMER, 'namer')
                name = fn(generator)
        self.name = name

        storage = storage or getattr(generator, 'cachefile_storage',
            None) or get_singleton(settings.IMAGEKIT_DEFAULT_FILE_STORAGE,
            'file storage backend')
        self.cachefile_backend = (
            cachefile_backend
            or getattr(generator, 'cachefile_backend', None)
            or get_singleton(settings.IMAGEKIT_DEFAULT_CACHEFILE_BACKEND,
                             'cache file backend'))
        self.cachefile_strategy = (
            cachefile_strategy
            or getattr(generator, 'cachefile_strategy', None)
            or get_singleton(settings.IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY,
                             'cache file strategy')
        )

        super(ImageCacheFile, self).__init__(storage=storage)

    def _require_file(self):
        if getattr(self, '_file', None) is None:
            content_required.send(sender=self, file=self)
            self._file = self.storage.open(self.name, 'rb')

    # The ``path`` and ``url`` properties are overridden so as to not call
    # ``_require_file``, which is only meant to be called when the file object
    # will be directly interacted with (e.g. when using ``read()``). These only
    # require the file to exist; they do not need its contents to work. This
    # distinction gives the user the flexibility to create a cache file
    # strategy that assumes the existence of a file, but can still make the file
    # available when its contents are required.

    def _storage_attr(self, attr):
        if getattr(self, '_file', None) is None:
            existence_required.send(sender=self, file=self)
        fn = getattr(self.storage, attr)
        return fn(self.name)

    @property
    def path(self):
        return self._storage_attr('path')

    @property
    def url(self):
        return self._storage_attr('url')

    def generate(self, force=False):
        """
        Generate the file. If ``force`` is ``True``, the file will be generated
        whether the file already exists or not.

        """
        if force or getattr(self, '_file', None) is None:
            self.cachefile_backend.generate(self, force)

    def _generate(self):
        # Generate the file
        content = generate(self.generator)

        actual_name = self.storage.save(self.name, content)

        # We're going to reuse the generated file, so we need to reset the pointer.
        content.seek(0)

        # Store the generated file. If we don't do this, the next time the
        # "file" attribute is accessed, it will result in a call to the storage
        # backend (in ``BaseIKFile._get_file``). Since we already have the
        # contents of the file, what would the point of that be?
        self.file = File(content)

        if actual_name != self.name:
            get_logger().warning(
                'The storage backend %s did not save the file with the'
                ' requested name ("%s") and instead used "%s". This may be'
                ' because a file already existed with the requested name. If'
                ' so, you may have meant to call generate() instead of'
                ' generate(force=True), or there may be a race condition in the'
                ' file backend %s. The saved file will not be used.' % (
                    self.storage,
                    self.name, actual_name,
                    self.cachefile_backend
                )
            )

    def __bool__(self):
        if not self.name:
            return False

        # Dispatch the existence_required signal before checking to see if the
        # file exists. This gives the strategy a chance to create the file.
        existence_required.send(sender=self, file=self)

        try:
            check = self.cachefile_strategy.should_verify_existence(self)
        except AttributeError:
            # All synchronous backends should have created the file as part of
            # `existence_required` if they wanted to.
            check = getattr(self.cachefile_backend, 'is_async', False)
        return self.cachefile_backend.exists(self) if check else True

    def __getstate__(self):
        state = copy(self.__dict__)

        # file is hidden link to "file" attribute
        state.pop('_file', None)

        return state

    def __nonzero__(self):
        # Python 2 compatibility
        return self.__bool__()

    def __repr__(self):
        return smart_str("<%s: %s>" % (
            self.__class__.__name__, self if self.name else "None")
        )


class LazyImageCacheFile(SimpleLazyObject):
    def __init__(self, generator_id, *args, **kwargs):
        def setup():
            generator = generator_registry.get(generator_id, *args, **kwargs)
            return ImageCacheFile(generator)
        super(LazyImageCacheFile, self).__init__(setup)

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, str(self) or 'None')
