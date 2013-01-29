from django.dispatch import Signal

before_access = Signal()
source_created = Signal(providing_args=[])
source_changed = Signal()
source_deleted = Signal()
