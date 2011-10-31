"""
Flushes and re-caches all images under ImageKit.

"""
from django.db.models.loading import cache
from django.core.management.base import BaseCommand

from imagekit.utils import get_spec_files


class Command(BaseCommand):
    help = ('Clears all ImageKit cached files.')
    args = '[apps]'
    requires_model_validation = True
    can_import_settings = True

    def handle(self, *args, **options):
        return flush_cache(args, options)


def flush_cache(apps, options):
    apps = [a.strip(',') for a in apps]
    if apps:
        for app_label in apps:
            app = cache.get_app(app_label)
            for model in [m for m in cache.get_models(app)]:
                print 'Flushing cache for "%s.%s"' % (app_label, model.__name__)
                for obj in model.objects.order_by('-pk'):
                    for spec_file in get_spec_files(obj):
                        if spec_file is not None:
                            spec_file.delete(save=False)
                        if spec_file.field.pre_cache:
                            spec_file._create()
    else:
        print 'Please specify one or more app names'
