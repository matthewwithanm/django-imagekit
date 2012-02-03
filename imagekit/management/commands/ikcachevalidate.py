from optparse import make_option
from django.core.management.base import BaseCommand
from django.db.models.loading import cache
from ...utils import validate_app_cache


class Command(BaseCommand):
    help = ('Validates the image cache for a list of apps.')
    args = '[apps]'
    requires_model_validation = True
    can_import_settings = True

    option_list = BaseCommand.option_list + (
        make_option('--force-revalidation',
            dest='force_revalidation',
            action='store_true',
            default=False,
            help='Invalidate each image file before validating it, thereby'
                    ' ensuring its revalidation. This is very similar to'
                    ' running ikcacheinvalidate and then running'
                    ' ikcachevalidate; the difference being that this option'
                    ' causes files to be invalidated and validated'
                    ' one-at-a-time, whereas running the two commands in series'
                    ' would invalidate all images before validating any.'
        ),
    )

    def handle(self, *args, **options):
        apps = args or cache.app_models.keys()
        validate_app_cache(apps, options['force_revalidation'])
