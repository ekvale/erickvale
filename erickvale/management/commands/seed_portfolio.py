"""Seed the personal portfolio grid (FeaturedApp) shown on the homepage.

Only apps with no login gate on their core public experience are included
here. allminnesota, dream_blue, braindump, mdh_briefings, projects, and
contacts are real operational / personal tools with private or sensitive
data and are deliberately left out of the public showcase.
"""
from django.core.management.base import BaseCommand
from erickvale.models import FeaturedApp

PROJECTS = [
    dict(
        slug='nomoar', name='NOMOAR', icon='✊', category='research', featured_size='large',
        url='https://nomoar.com', order=1,
        tagline='A civic history site most people never got to learn in school.',
        description=(
            'Timeline and map of redlining, the Chinese Exclusion Act, the Tulsa Race Massacre, and a lot '
            'more. It has lesson kits for teachers, an embeddable widget, RSS and JSON feeds, and a queue '
            'where people can submit their own entries. Probably the most complete thing I have built.'
        ),
        features=['Interactive timeline + map', 'Educator lesson kits', 'Embeddable widgets & feeds', 'Community submissions with moderation'],
    ),
    dict(
        slug='math-bastion', name='Math Bastion', icon='🏰', category='games', featured_size='large',
        url='/apps/math-bastion/', order=2,
        tagline='An idle tower defense where the only way to level up is long division.',
        description=(
            'One bastion, waves that never stop, and a real math trial gating every new era, from tally '
            'marks all the way to calculus. Runs right in your browser. No download.'
        ),
        features=['Endless scaling waves + bosses', 'Math trials gate progression', 'Server-backed wallet & leaderboard', 'Canvas + WebAudio, no assets'],
    ),
    dict(
        slug='stratum-health', name='Stratum Health', icon='🧬', category='data', featured_size='large',
        url='https://stratum-health.com', order=3,
        tagline='The professional side of what I do: health data infrastructure.',
        description=(
            'A federated OMOP pipeline I built for the Minnesota Electronic Health Record Consortium. It '
            'links records privately across health systems and estimates disease prevalence for people '
            'public health surveillance usually misses. This one is also my consulting practice.'
        ),
        features=['Federated OMOP CDM pipeline', 'HMAC-based record linkage', 'Live 7-step pipeline demo', 'Suppressed prevalence estimates'],
    ),
    dict(
        slug='chess-trainer', name='Chess Trainer', icon='♟️', category='games', featured_size='normal',
        url='/chess/', order=4,
        tagline='Spaced repetition, but for chess openings.',
        description=(
            'Drills chess openings with an SM-2 style spaced repetition scheduler, so it tracks your '
            'mastery and streaks lesson by lesson instead of just quizzing you at random.'
        ),
        features=['SM-2 spaced repetition', 'Opening drills & quizzes', 'Mastery & streak tracking'],
    ),
    dict(
        slug='arm-chair-detective', name='Arm Chair Detective', icon='🔍', category='games', featured_size='normal',
        url='/apps/arm-chair-detective/', order=5,
        tagline='100,000 suspects. One culprit. Your filters.',
        description=(
            'A deduction game that actually plays like detective work. You get eyewitness accounts, 911 '
            'transcripts, and video analysis, then narrow a huge suspect pool down with filters until only '
            'one person is left.'
        ),
        features=['Large filterable suspect pools', 'Eyewitness & 911 clue system', 'Realistic deduction workflow'],
    ),
    dict(
        slug='personality-game', name='Read the Room', icon='🎭', category='games', featured_size='normal',
        url='/apps/personality-game/', order=6,
        tagline='Can you read the room before you respond?',
        description=(
            'Watch a negotiation play out, name the other person’s style, then pick the response that '
            'actually works. It is scored and streaked, with a training mode for the tells you keep missing.'
        ),
        features=['Negotiation scenario engine', 'Streak scoring', 'Training mode with hints'],
    ),
    dict(
        slug='card-maker', name='Card Maker', icon='🃏', category='tools', featured_size='normal',
        url='/apps/cards/', order=7,
        tagline='A card generator that designs its own cards.',
        description=(
            'Give it stats and flavor text and it composites a finished trading card for you: RPG stat '
            'blocks, rarity tiers, custom sets, all rendered as real PNGs.'
        ),
        features=['Auto-composited card images', 'RPG stat blocks & rarity tiers', 'Custom sets & collections'],
    ),
    dict(
        slug='literary-analysis', name='Literary Analysis', icon='📖', category='research', featured_size='normal',
        url='/apps/literary/', order=8,
        tagline='Turning a close reading of Dhalgren into actual data.',
        description=(
            'A full qualitative coding workflow (codebooks, tagged text segments, analytical memos, '
            'frequency reports) built around my own line-by-line coding of Delany’s Dhalgren. Generic '
            'enough to use on any text, though.'
        ),
        features=['Custom codebooks', 'Tagged text segments & memos', 'Code-frequency reports', 'CSV/JSON export'],
    ),
    dict(
        slug='blog', name='Blog', icon='✍️', category='research', featured_size='normal',
        url='/apps/blog/', order=9,
        tagline='Notes on whatever I’m building this month.',
        description='The running commentary behind these projects. What worked, what did not, and what is next.',
        features=['Monthly project write-ups', 'Development notes'],
    ),
]


class Command(BaseCommand):
    help = 'Seed (or refresh) the public portfolio grid shown on the homepage.'

    def handle(self, *args, **options):
        for data in PROJECTS:
            slug = data.pop('slug')
            data['is_published'] = True
            _obj, created = FeaturedApp.objects.update_or_create(slug=slug, defaults=data)
            self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Updated"} {data["name"]}'))
        self.stdout.write(self.style.SUCCESS(f'Seeded {len(PROJECTS)} portfolio projects.'))
