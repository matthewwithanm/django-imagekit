from django.dispatch import Signal

source_created = Signal(providing_args=[])
source_changed = Signal()
source_deleted = Signal()
