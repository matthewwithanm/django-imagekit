from django.utils.importlib import import_module
import re
import sys


class ProcessorImporter(object):
    """
    The processors were moved to the PILKit project so they could be used
    separtely from ImageKit (which has a bunch of Django dependencies). However,
    there's no real need to expose this fact (and we want to maintain backwards
    compatibility), so we proxy all "imagekit.processors" imports to
    "pilkit.processors" using this object.

    """
    pattern = re.compile(r'^imagekit\.processors((\..*)?)$')

    def find_module(self, name, path=None):
        if self.pattern.match(name):
            return self

    def load_module(self, name):
        if name in sys.modules:
            return sys.modules[name]

        new_name = self.pattern.sub(r'pilkit.processors\1', name)
        return import_module(new_name)


sys.meta_path.append(ProcessorImporter())
