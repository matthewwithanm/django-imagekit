from django.core.management.base import BaseCommand
import re
from ...files import ImageSpecCacheFile
from ...specs import registry


class Command(BaseCommand):
    help = ('Warm the image cache for the specified specs (or all specs if none'
            ' was provided). Simple wildcard matching (using asterisks) is'
            ' supported.')
    args = '[spec_ids]'

    def handle(self, *args, **options):
        specs = registry.get_spec_ids()

        if args:
            patterns = self.compile_patterns(args)
            specs = (id for id in specs if any(p.match(id) for p in patterns))

        for spec_id in specs:
            self.stdout.write('Validating spec: %s\n' % spec_id)
            spec = registry.get_spec(spec_id)  # TODO: HINTS! (Probably based on source, so this will need to be moved into loop below.)
            for source in registry.get_sources(spec_id):
                for source_file in source.files():
                    if source_file:
                        self.stdout.write('  %s\n' % source_file)
                        try:
                            # TODO: Allow other validation actions through command option
                            ImageSpecCacheFile(spec, source_file).validate()
                        except Exception, err:
                            # TODO: How should we handle failures? Don't want to error, but should call it out more than this.
                            self.stdout.write('    FAILED: %s\n' % err)

    def compile_patterns(self, spec_ids):
        return [re.compile('%s$' % '.*'.join(re.escape(part) for part in id.split('*'))) for id in spec_ids]
