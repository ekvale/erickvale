"""Load suggested default tags for the Rights Archive."""
from django.core.management.base import BaseCommand
from human_rights_archive.models import Tag


# (slug, name, category, keywords)
# keywords: comma-separated; if any appear in article title/summary/content, this tag is applied.
DEFAULTS = [
    ('human-rights-violations', 'Human rights violations', 'human rights', 'human rights violation,human rights abuse'),
    ('constitutional-violations', 'Constitutional violations', 'constitutional', 'constitutional violation'),
    ('first-amendment', '1st Amendment', 'constitutional', 'first amendment,1st amendment,freedom of speech,freedom of religion'),
    ('fourth-amendment', '4th Amendment', 'constitutional', 'fourth amendment,4th amendment,unreasonable search,unreasonable seizure'),
    ('fifth-amendment', '5th Amendment', 'constitutional', 'fifth amendment,5th amendment,due process,self-incrimination'),
    ('eighth-amendment', '8th Amendment', 'constitutional', 'eighth amendment,8th amendment,cruel and unusual,excessive bail'),
    ('police-misconduct', 'Police misconduct / excessive force', 'government', 'police misconduct,excessive force,police brutality'),
    ('government-overreach', 'Government overreach / abuse of power', 'government', 'government overreach,abuse of power'),
    ('civil-liberties', 'Civil liberties (speech, assembly, privacy)', 'civil liberties', 'civil liberties,civil rights'),
    ('discrimination', 'Discrimination / equal protection', 'civil liberties', 'discrimination,equal protection'),
    ('prison-conditions', 'Prison / detention conditions', 'human rights', 'prison conditions,detention conditions,inmate,jail conditions'),
    ('immigration-enforcement', 'Immigration enforcement / family separation', 'immigration', 'immigration enforcement,family separation,separated families,border enforcement'),
    ('freedom-of-the-press', 'Freedom of the press / reporter harassment', 'civil liberties', 'freedom of the press,press freedom,reporter harassment,journalist'),
    ('whistleblower-retaliation', 'Whistleblower retaliation', 'government', 'whistleblower,retaliation'),
    # ICE / U.S. immigration enforcement
    ('ice', 'ICE (U.S. Immigration and Customs Enforcement)', 'immigration', 'ICE,Immigration and Customs Enforcement,immigration enforcement'),
    ('cbp', 'CBP (Customs and Border Protection)', 'immigration', 'CBP,Customs and Border Protection,border patrol,Border Patrol'),
    ('dhs', 'DHS (Department of Homeland Security)', 'immigration', 'DHS,Department of Homeland Security,homeland security'),
    ('immigration-detention', 'Immigration detention', 'immigration', 'immigration detention,detention center,detention facility,detained immigrants,ICE detention,migrant detention'),
    ('family-separation', 'Family separation at border', 'immigration', 'family separation,separated families,border separation'),
    ('deportation', 'Deportation / removal', 'immigration', 'deportation,deport,removal,removed,expelled'),
    ('asylum', 'Asylum / refugees', 'immigration', 'asylum,asylum seeker,refugee,migrant,Title 42'),
    ('border', 'U.S.-Mexico border', 'immigration', 'U.S.-Mexico border,border crisis,border wall,southern border'),
]

class Command(BaseCommand):
    help = 'Load default tags for the Human Rights Archive (including ICE/immigration tags with auto-tag keywords)'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Remove all tags first (destructive)')
        parser.add_argument('--ice-only', action='store_true', help='Add only ICE/immigration-related tags')

    def handle(self, *args, **options):
        if options.get('clear'):
            n = Tag.objects.count()
            Tag.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Removed {n} tags.'))
        to_load = DEFAULTS
        if options.get('ice_only'):
            to_load = [t for t in DEFAULTS if t[2] == 'immigration' or 'ice' in t[0] or 'cbp' in t[0] or 'dhs' in t[0] or 'immigration' in t[0] or 'detention' in t[0] or 'family-separation' in t[0] or 'deportation' in t[0] or 'asylum' in t[0] or 'border' in t[0]]
        created = 0
        updated = 0
        for slug, name, category, keywords in to_load:
            obj, c = Tag.objects.update_or_create(
                slug=slug,
                defaults={'name': name, 'category': category, 'keywords': keywords or ''},
            )
            if c:
                created += 1
            else:
                updated += 1
        self.stdout.write(self.style.SUCCESS(f'Created {created}, updated {updated}. Total tags: {Tag.objects.count()}'))
