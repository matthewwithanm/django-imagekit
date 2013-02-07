from django.core.management.base import BaseCommand
import re
from ...registry import generator_registry, cachefile_registry


class Command(BaseCommand):
    help = ("""Generate files for the specified image generators (or all of them if
none was provided). Simple, glob-like wildcards are allowed, with *
matching all characters within a segment, and ** matching across
segments. (Segments are separated with colons.) So, for example,
"a:*:c" will match "a:b:c", but not "a:b:x:c", whereas "a:**:c" will
match both. Subsegments are always matched, so "a" will match "a" as
well as "a:b" and "a:b:c".""")
    args = '[generator_ids]'

    def handle(self, *args, **options):
        generators = generator_registry.get_ids()

        if args:
            patterns = self.compile_patterns(args)
            generators = (id for id in generators if any(p.match(id) for p in patterns))

        for generator_id in generators:
            self.stdout.write('Validating generator: %s\n' % generator_id)
            for file in cachefile_registry.get(generator_id):
                self.stdout.write('  %s\n' % file)
                try:
                    # TODO: Allow other validation actions through command option
                    file.generate()
                except Exception, err:
                    # TODO: How should we handle failures? Don't want to error, but should call it out more than this.
                    self.stdout.write('    FAILED: %s\n' % err)

    def compile_patterns(self, generator_ids):
        return [self.compile_pattern(id) for id in generator_ids]

    def compile_pattern(self, generator_id):
        parts = re.split(r'(\*{1,2})', generator_id)
        pattern = ''
        for part in parts:
            if part == '*':
                pattern += '[^:]*'
            elif part == '**':
                pattern += '.*'
            else:
                pattern += re.escape(part)
        return re.compile('^%s(:.*)?$' % pattern)
