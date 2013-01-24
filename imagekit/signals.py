from django.dispatch import Signal

before_access = Signal()
cacheable_created = Signal(providing_args=[])
cacheable_changed = Signal()
cacheable_deleted = Signal()
