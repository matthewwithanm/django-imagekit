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
    
    option_list = BaseCommand.option_list + (
        make_option("-c", "--spec_class", dest="spec_class", action='append'),
    )
    def handle(self, *args, **options):
        return flush_cache(args, options)

def flush_cache(apps, options):
    """ Clears the image cache
    
    """
    spec_class_list = options['spec_class']
    apps = [a.strip(',') for a in apps]
    if apps:
        for app_label in apps:
            app = cache.get_app(app_label)    
            models = [m for m in cache.get_models(app) if issubclass(m, ImageModel)]
            for model in models:
                print('Flushing cache for "%s.%s"' % (app_label, model.__name__))
                for obj in model.objects.all():
                    if spec_class_list:
                        for spec_name in spec_class_list:
                            try:
                                spec = model._ik.specs[spec_name]
                            except KeyError:
                                print('Model %s has no spec named %s' % (model.__name__, spec_name))
                                continue
                            prop = getattr(obj, spec.name(), None)
                            if prop is not None:
                                prop._delete()
                            if spec.pre_cache:
                                print('Creating %s: %d' % (spec_name,obj.id))
                                prop._create()
                    else:
                        for spec in model._ik.specs:
                            prop = getattr(obj, spec.name(), None)
                            if prop is not None:
                                prop._delete()
                            if spec.pre_cache:
                                prop._create()
    else:
        print 'Please specify on or more app names'
