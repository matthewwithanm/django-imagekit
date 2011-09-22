# Imagekit options
import os
import os.path


class Options(object):
    """ Class handling per-model imagekit options

    """

    preprocessor_spec = None
    save_count_as = None

    def __init__(self, opts):
        for key, value in opts.__dict__.iteritems():
            setattr(self, key, value)
