"""Load suggested default tags for the Rights Archive."""
from django.core.management.base import BaseCommand
from human_rights_archive.models import Tag


DEFAULTS = [
    ('human-rights-violations', 'Human rights violations', 'human rights'),
    ('constitutional-violations', 'Constitutional violations', 'constitutional'),
    ('first-amendment', '1st Amendment', 'constitutional'),
    ('fourth-amendment', '4th Amendment', 'constitutional'),
    ('fifth-amendment', '5th Amendment', 'constitutional'),
    ('eighth-amendment', '8th Amendment', 'constitutional'),
    ('police-misconduct', 'Police misconduct / excessive force', 'government'),
    ('government-overreach', 'Government overreach / abuse of power', 'government'),
    ('civil-liberties', 'Civil liberties (speech, assembly, privacy)', 'civil liberties'),
    ('discrimination', 'Discrimination / equal protection', 'civil liberties'),
    ('prison-conditions', 'Prison / detention conditions', 'human rights'),
    ('immigration-enforcement', 'Immigration enforcement / family separation', 'government'),
    ('freedom-of-the-press', 'Freedom of the press / reporter harassment', 'civil liberties'),
    ('whistleblower-retaliation', 'Whistleblower retaliation', 'government'),
]


class Command(BaseCommand):
    help = 'Load default tags for the Human Rights Archive'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Remove all tags first (destructive)')

    def handle(self, *args, **options):
        if options.get('clear'):
            n = Tag.objects.count()
            Tag.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Removed {n} tags.'))
        created = 0
        for slug, name, category in DEFAULTS:
            _, c = Tag.objects.get_or_create(slug=slug, defaults={'name': name, 'category': category})
            if c:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'Created {created} new tags. Total: {Tag.objects.count()}'))
