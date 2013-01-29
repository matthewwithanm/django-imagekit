from django.core.management.base import BaseCommand
import re
from ...registry import generator_registry, cacheable_registry


class Command(BaseCommand):
    help = ('Warm the image cache for the specified generators'
            ' (or all generators if none was provided).'
            ' Simple wildcard matching (using asterisks) is supported.')
    args = '[generator_ids]'

    def handle(self, *args, **options):
        generators = generator_registry.get_ids()

        if args:
            patterns = self.compile_patterns(args)
            generators = (id for id in generators if any(p.match(id) for p in patterns))

        for generator_id in generators:
            self.stdout.write('Validating generator: %s\n' % generator_id)
            for cacheable in cacheable_registry.get(generator_id):
                self.stdout.write('  %s\n' % cacheable)
                try:
                    # TODO: Allow other validation actions through command option
                    cacheable.validate()
                except Exception, err:
                    # TODO: How should we handle failures? Don't want to error, but should call it out more than this.
                    self.stdout.write('    FAILED: %s\n' % err)

    def compile_patterns(self, generator_ids):
        return [re.compile('%s$' % '.*'.join(re.escape(part) for part in id.split('*'))) for id in generator_ids]
