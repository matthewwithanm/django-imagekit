from django.db.models.loading import cache
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from imagekit.utils import get_bound_specs


class Command(BaseCommand):
    help = ('Clears all ImageKit cached files.')
    args = '[apps]'
    requires_model_validation = True
    can_import_settings = True

    def handle(self, *args, **options):
        return flush_cache(args, options)

def flush_cache(apps, options):
    """ Clears the image cache

    """
    apps = [a.strip(',') for a in apps]
    if apps:
        for app_label in apps:
            app = cache.get_app(app_label)
            for model in [m for m in cache.get_models(app)]:
                print 'Flushing cache for "%s.%s"' % (app_label, model.__name__)
                for obj in model.objects.order_by('-id'):
                    for spec in get_bound_specs(obj):
                        if spec is not None:
                            spec._delete()
                        if spec.pre_cache:
                            spec._create()
    else:
        print 'Please specify on or more app names'
