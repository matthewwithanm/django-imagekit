from django.db.models.loading import cache
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from imagekit.models import ImageModel
from imagekit.specs import ImageSpec


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
            models = [m for m in cache.get_models(app) if issubclass(m, ImageModel)]
            for model in models:
                print 'Flushing cache for "%s.%s"' % (app_label, model.__name__)
                for obj in model.objects.all():
                    for spec in model._ik.specs:
                        prop = getattr(obj, spec.name(), None)
                        if prop is not None:
                            prop._delete()
                        if spec.pre_cache:
                            prop._create()
    else:
        print 'Please specify on or more app names'
