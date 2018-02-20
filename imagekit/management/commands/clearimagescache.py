from django.core.management.base import BaseCommand
from ...utils import get_cache


class Command(BaseCommand):
    help = 'Clear images cache'

    def handle(self, *args, **options):
        get_cache().clear()
