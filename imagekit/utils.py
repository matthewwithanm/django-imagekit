""" ImageKit utility functions """

import tempfile

def img_to_fobj(img, format, **kwargs):
    tmp = tempfile.TemporaryFile()
    img.convert('RGB').save(tmp, format, **kwargs)
    tmp.seek(0)
    return tmp


def get_bound_specs(instance):
    from imagekit.fields import BoundImageSpec
    bound_specs = []
    for key in dir(instance):
        try:
            value = getattr(instance, key)
        except AttributeError:
            continue
        if isinstance(value, BoundImageSpec):
            bound_specs.append(value)
    return bound_specs
