from copy import copy
from hashlib import md5
from pickle import MARK, DICT
try:
    from pickle import _Pickler
except ImportError:
    # Python 2 compatible
    from pickle import Pickler as _Pickler
from .lib import StringIO


class CanonicalizingPickler(_Pickler):
    dispatch = copy(_Pickler.dispatch)

    def save_set(self, obj):
        rv = obj.__reduce_ex__(0)
        rv = (rv[0], (sorted(rv[1][0]),), rv[2])
        self.save_reduce(obj=obj, *rv)

    dispatch[set] = save_set

    def save_dict(self, obj):
        write = self.write
        write(MARK + DICT)

        self.memoize(obj)
        self._batch_setitems(sorted(obj.items()))

    dispatch[dict] = save_dict


def pickle(obj):
    file = StringIO()
    CanonicalizingPickler(file, 0).dump(obj)
    return md5(file.getvalue()).hexdigest()
