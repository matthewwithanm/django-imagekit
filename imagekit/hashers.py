from copy import copy
from hashlib import md5
from pickle import Pickler, MARK, DICT
from types import DictionaryType
from .lib import StringIO


class CanonicalizingPickler(Pickler):
    dispatch = copy(Pickler.dispatch)

    def save_set(self, obj):
        rv = obj.__reduce_ex__(0)
        rv = (rv[0], (sorted(rv[1][0]),), rv[2])
        self.save_reduce(obj=obj, *rv)

    dispatch[set] = save_set

    def save_dict(self, obj):
        write = self.write
        write(MARK + DICT)

        self.memoize(obj)
        self._batch_setitems(sorted(obj.iteritems()))

    dispatch[DictionaryType] = save_dict


def pickle(obj):
    file = StringIO()
    CanonicalizingPickler(file, 0).dump(obj)
    return md5(file.getvalue()).hexdigest()
