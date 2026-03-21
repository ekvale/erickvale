"""
Idempotent sample rows for NOMOAR engagement models (paths, kits, glossary, etc.).
Requires existing HistoricalEvent rows (run nomoar_seed_from_fixture first).

  python manage.py nomoar_seed_sample_content
"""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db.models import Max
from django.utils import timezone

from nomoar.models import (
    ArchiveNewsPost,
    Collection,
    EngagementConfig,
    EventSource,
    GlossaryTerm,
    HistoricalEvent,
    LearningPath,
    LearningPathStep,
    LessonKit,
    LocalizedResourcePack,
    NewsletterSubscriber,
)


def _event(slug):
    return HistoricalEvent.objects.filter(slug=slug).first()


def _static_sample_pdf_path():
    return Path(settings.BASE_DIR) / 'nomoar' / 'static' / 'nomoar' / 'samples' / 'sample-poster.pdf'


class Command(BaseCommand):
    help = 'Seed sample learning path, poster PDFs, glossary, commentary, collections, etc.'

    def handle(self, *args, **options):
        if not HistoricalEvent.objects.exists():
            self.stderr.write(
                self.style.ERROR('No events in DB. Run: python manage.py nomoar_seed_from_fixture'),
            )
            return

        pdf_path = _static_sample_pdf_path()
        if not pdf_path.is_file():
            self.stderr.write(self.style.WARNING(f'Missing static PDF at {pdf_path}; skipping file copies'))

        n = 0

        # --- EngagementConfig: fill placeholders if empty ---
        ec = EngagementConfig.get_solo()
        updated = []
        if not (ec.donation_url or '').strip():
            ec.donation_url = (
                'https://www.gofundme.com/f/support-nomoar-national-online-museum-of-american-racism'
            )
            updated.append('donation_url')
        if not (ec.membership_url or '').strip():
            ec.membership_url = 'https://nomoar.org/'
            updated.append('membership_url')
        if not (ec.grants_fiscal_sponsorship_blurb or '').strip():
            ec.grants_fiscal_sponsorship_blurb = (
                'We welcome inquiries from foundations and fiscal sponsors supporting public history '
                'and anti-racist education. Contact the site operator with a brief project summary.'
            )
            updated.append('grants_fiscal_sponsorship_blurb')
        if not (ec.museum_services_blurb or '').strip():
            ec.museum_services_blurb = (
                'Custom data ingest, white-label timeline/map views, and training for staff are '
                'available as paid services on a case-by-case basis.'
            )
            updated.append('museum_services_blurb')
        if not ec.api_partnerships_url.strip():
            ec.api_partnerships_url = 'https://github.com/ekvale/erickvale'
            updated.append('api_partnerships_url')
        if updated:
            ec.save(update_fields=updated)
            self.stdout.write(self.style.SUCCESS(f'EngagementConfig updated: {", ".join(updated)}'))
            n += 1

        # --- Sample collection (partner-style) + general thematic collection ---
        col_partner, cr = Collection.objects.update_or_create(
            slug='sample-partner-spotlight-demo',
            defaults={
                'title': 'Sample partner spotlight: Public history network',
                'description': (
                    'Demonstration collection showing how a library or museum partner can group '
                    'entries with a byline and optional sponsor disclosure. Replace copy in admin.'
                ),
                'order': 90,
                'is_published': True,
                'is_partner_spotlight': True,
                'partner_organization': 'Demo Public History Network (sample)',
                'partner_url': 'https://nomoar.org/',
                'guest_byline': 'Guest introduction: sample text for educator partners.',
                'sponsor_disclosure': (
                    'This sample collection is not sponsored. If you accept underwriting, describe it '
                    'here; it does not change search or related-entry ranking.'
                ),
            },
        )
        self.stdout.write(self.style.SUCCESS(f'Collection: {col_partner.slug} (created={cr})'))
        n += 1

        col_theme, cr2 = Collection.objects.update_or_create(
            slug='sample-federal-lands-and-memory',
            defaults={
                'title': 'Federal lands, memory, and contested history',
                'description': (
                    'Sample thematic grouping aligned with several seed events about parks, monuments, '
                    'and interpretation.'
                ),
                'order': 91,
                'is_published': True,
                'is_partner_spotlight': False,
            },
        )
        self.stdout.write(self.style.SUCCESS(f'Collection: {col_theme.slug} (created={cr2})'))
        n += 1

        for slug in (
            'executive-order-14253-restoring-truth-and-sanity',
            'muir-woods-history-under-construction-exhibit-removal',
            'grand-canyon-indigenous-displacement-references-removed',
            'stonewall-national-monument-lgbtq-history-altered',
        ):
            ev = _event(slug)
            if ev:
                col_theme.events.add(ev)
                col_partner.events.add(ev)

        # --- Learning path ---
        path, pr = LearningPath.objects.update_or_create(
            slug='sample-path-federal-lands-and-truth',
            defaults={
                'title': 'Sample path: Federal lands, truth, and community response',
                'intro': (
                    'This is a sample learning path for high school or introductory college classes. '
                    'Walk through four entries in order; use each instructor note as a warm-up or exit '
                    'ticket. Swap events in admin to match your syllabus.'
                ),
                'theme_place_decade_note': 'United States · 2025–2026 · Policy & memory',
                'order': 1,
                'is_published': True,
            },
        )
        LearningPathStep.objects.filter(path=path).delete()
        steps = [
            (
                0,
                'executive-order-14253-restoring-truth-and-sanity',
                'Opening frame: What does “restoring” history mean when the state rewrites public land interpretation?',
            ),
            (
                1,
                'muir-woods-history-under-construction-exhibit-removal',
                'Compare conservation narratives with Indigenous history. Who is centered in each version?',
            ),
            (
                2,
                'grand-canyon-indigenous-displacement-references-removed',
                'Map check: find Grand Canyon on the archive map. What is lost when displacement is erased from signage?',
            ),
            (
                3,
                'stonewall-national-monument-lgbtq-history-altered',
                'Closing: connect erasure at Stonewall to patterns you saw in earlier steps.',
            ),
        ]
        for order, ev_slug, note in steps:
            ev = _event(ev_slug)
            if ev:
                LearningPathStep.objects.create(path=path, event=ev, order=order, instructor_note=note)
        self.stdout.write(self.style.SUCCESS(f'LearningPath: {path.slug} with {path.steps.count()} steps'))
        n += 1

        # --- Lesson kit (linked to path) ---
        kit, kr = LessonKit.objects.update_or_create(
            slug='sample-lesson-map-timeline-101',
            defaults={
                'title': 'Sample lesson: Map + timeline 101',
                'summary': 'One-period introduction using the archive map, timeline filters, and embeddable slice.',
                'standards_alignment': (
                    'Sample alignment text: replace with your state social studies or media-literacy standards.'
                ),
                'discussion_prompts': (
                    '1) Why might governments change what appears on federal land signage?\n'
                    '2) How do map and timeline views change what students notice first?\n'
                    '3) Where would students look for primary evidence beyond the archive summary?'
                ),
                'map_timeline_activity': (
                    '1) Open the Timeline; filter by decade or state.\n'
                    '2) Open the Map with the same filters (use “Timeline (same filters)” or “Map (same filters)”).\n'
                    '3) Embed a slice on your LMS: copy the “Filtered list embed” URL from any event page '
                    'and adjust query params (state, decade, q, location).\n'
                    '4) Optional: print the sample poster SVG from static files for a gallery walk.'
                ),
                'body': (
                    'This kit is demo content. Attach your own PDF in admin or link to district resources.\n\n'
                    'Static sample poster (SVG): after collectstatic, use '
                    '/static/nomoar/samples/sample-poster.svg\n'
                ),
                'related_path': path,
                'order': 1,
                'is_published': True,
            },
        )
        if pdf_path.is_file() and not kit.pdf_file:
            with pdf_path.open('rb') as f:
                kit.pdf_file.save('sample-lesson-one-pager.pdf', File(f), save=True)
            self.stdout.write('  attached sample PDF to lesson kit')
        n += 1

        # --- Glossary terms ---
        gloss_specs = [
            (
                'redlining',
                'Redlining',
                (
                    'Redlining describes how government and private maps and policies steered credit and '
                    'insurance away from neighborhoods graded “hazardous,” often on racial grounds. '
                    'The archive includes HOLC-era security maps as a policy artifact.'
                ),
                ['holc-redlining-security-maps-new-deal'],
            ),
            (
                'chinese-exclusion-act',
                'Chinese Exclusion Act (1882)',
                (
                    'Federal law that restricted immigration of Chinese laborers and shaped decades of '
                    'anti-Asian policy. Useful for connecting legislation to longer arcs of discrimination.'
                ),
                ['chinese-exclusion-act-1882'],
            ),
            (
                'executive-order',
                'Executive order (sample glossary entry)',
                (
                    'Executive orders direct how the executive branch operates; they can reshape interpretation '
                    'on federal lands and museums. Compare text and implementation across administrations.'
                ),
                ['executive-order-14253-restoring-truth-and-sanity'],
            ),
        ]
        for slug, title, definition, ev_slugs in gloss_specs:
            gt, gr = GlossaryTerm.objects.update_or_create(
                slug=slug,
                defaults={'title': title, 'definition': definition, 'order': 10},
            )
            rel = []
            for es in ev_slugs:
                ev = _event(es)
                if ev:
                    rel.append(ev)
            gt.related_events.set(rel)
            self.stdout.write(self.style.SUCCESS(f'GlossaryTerm: {slug} (created={gr})'))
            n += 1

        # --- Commentary post ---
        post, por = ArchiveNewsPost.objects.update_or_create(
            slug='sample-commentary-erasure-and-parks-2025',
            defaults={
                'title': 'Sample commentary: Erasure and public land history (2025)',
                'teaser': (
                    'Demonstration blog-style post linking current patterns to several archive entries—replace '
                    'with your own editorial workflow.'
                ),
                'body': (
                    'This is sample commentary for the Archive in the news section. In a real post, '
                    'you might connect a current headline to documented patterns: removal of exhibits, '
                    'changes to monument interpretation, or shifts in federal language about slavery, '
                    'Indigenous nations, or LGBTQ+ history.\n\n'
                    'The related entries below are seeded examples; curate your own links in admin.'
                ),
                'published_at': timezone.now(),
                'is_published': True,
            },
        )
        rel_ev = [
            _event(s)
            for s in (
                'presidents-house-slavery-exhibit-removal-philadelphia',
                'stonewall-national-monument-lgbtq-history-altered',
                'grand-canyon-indigenous-displacement-references-removed',
            )
        ]
        post.related_events.set([e for e in rel_ev if e])
        self.stdout.write(self.style.SUCCESS(f'ArchiveNewsPost: {post.slug} (created={por})'))
        n += 1

        # --- Localized resource pack + poster PDF ---
        pack, par = LocalizedResourcePack.objects.update_or_create(
            slug='sample-pack-philadelphia-memory',
            defaults={
                'title': 'Sample localized pack: Philadelphia memory & justice',
                'description': (
                    'Demonstration pack for a city slice: use the timeline location filter and optional '
                    'printable PDF for a neighborhood history night.'
                ),
                'city': 'Philadelphia',
                'county': '',
                'state': 'PA',
                'embed_slice_hint': (
                    'Try: ?state=PA&q=Philadelphia&limit=15\n'
                    'Or timeline: ?location=Independence National Historical Park, Philadelphia, Pennsylvania\n'
                    '(exact string must match an event location field).'
                ),
                'order': 1,
                'is_published': True,
            },
        )
        if pdf_path.is_file() and not pack.printable_pdf:
            with pdf_path.open('rb') as f:
                pack.printable_pdf.save('sample-localized-poster.pdf', File(f), save=True)
            self.stdout.write('  attached sample PDF to localized pack')
        n += 1

        # --- Demo newsletter subscribers (obvious test addresses) ---
        for email, notes in (
            ('educator-demo@example.com', 'Sample row — safe to delete'),
            ('library-partner-demo@example.com', 'Sample row — safe to delete'),
        ):
            obj, nr = NewsletterSubscriber.objects.get_or_create(
                email=email,
                defaults={'active': True, 'notes': notes},
            )
            if nr:
                self.stdout.write(f'NewsletterSubscriber: {email}')
                n += 1

        # --- Primary source sample on one event ---
        gc = _event('grand-canyon-indigenous-displacement-references-removed')
        if gc:
            sample_url = 'https://www.nps.gov/grca/learn/index.htm'
            if not EventSource.objects.filter(event=gc, url=sample_url).exists():
                max_order = EventSource.objects.filter(event=gc).aggregate(m=Max('order'))['m']
                next_order = (max_order + 1) if max_order is not None else 0
                EventSource.objects.create(
                    event=gc,
                    order=next_order,
                    source_kind=EventSource.SourceKind.LINK,
                    citation='Sample primary source row (replace with real NPS or press citation)',
                    url=sample_url,
                    context_note=(
                        'For classrooms: ask students to compare official park interpretation with tribal '
                        'nations’ own histories and news coverage. This URL is a placeholder landing page.'
                    ),
                )
                self.stdout.write(self.style.SUCCESS('EventSource sample on Grand Canyon event'))
                n += 1

        self.stdout.write(self.style.SUCCESS(f'Done. Sample objects touched/created: ~{n}+ (collections M2M, etc.)'))
