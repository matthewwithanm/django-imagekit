from django.core.management.base import BaseCommand
import re
from ...files import GeneratedImageCacheFile
from ...registry import generator_registry, source_group_registry


class Command(BaseCommand):
    help = ('Warm the image cache for the specified specs (or all specs if none'
            ' was provided). Simple wildcard matching (using asterisks) is'
            ' supported.')
    args = '[spec_ids]'

    def handle(self, *args, **options):
        specs = generator_registry.get_ids()

        if args:
            patterns = self.compile_patterns(args)
            specs = (id for id in specs if any(p.match(id) for p in patterns))

        for spec_id in specs:
            self.stdout.write('Validating spec: %s\n' % spec_id)
            spec = generator_registry.get(spec_id)  # TODO: HINTS! (Probably based on source, so this will need to be moved into loop below.)
            for source in source_group_registry.get(spec_id):
                for source_file in source.files():
                    if source_file:
                        self.stdout.write('  %s\n' % source_file)
                        try:
                            # TODO: Allow other validation actions through command option
                            GeneratedImageCacheFile(spec, source_file=source_file).validate()
                        except Exception, err:
                            # TODO: How should we handle failures? Don't want to error, but should call it out more than this.
                            self.stdout.write('    FAILED: %s\n' % err)

    def compile_patterns(self, spec_ids):
        return [re.compile('%s$' % '.*'.join(re.escape(part) for part in id.split('*'))) for id in spec_ids]
