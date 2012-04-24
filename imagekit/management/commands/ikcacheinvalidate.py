from django.core.management.base import BaseCommand
from django.db.models.loading import cache
from ...utils import invalidate_app_cache


class Command(BaseCommand):
    help = ('Invalidates the image cache for a list of apps.')
    args = '[apps]'
    requires_model_validation = True
    can_import_settings = True

    def handle(self, *args, **options):
        apps = args or cache.app_models.keys()
        invalidate_app_cache(apps)
