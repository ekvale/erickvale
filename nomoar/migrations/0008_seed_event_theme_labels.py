# Data migration: theme labels + assignments by event slug

from django.db import migrations


def seed_theme_labels(apps, schema_editor):
    EventThemeLabel = apps.get_model('nomoar', 'EventThemeLabel')
    HistoricalEvent = apps.get_model('nomoar', 'HistoricalEvent')

    defs = [
        (0, 'institutional', 'Institutional'),
        (1, 'cultural', 'Cultural'),
        (2, 'court-case', 'Court case'),
    ]
    labels = {}
    for order, slug, name in defs:
        obj, _ = EventThemeLabel.objects.get_or_create(
            slug=slug,
            defaults={'name': name, 'order': order},
        )
        labels[slug] = obj

    # event_slug -> label slugs (event_type pill is rendered separately on cards)
    mapping = {
        'grand-canyon-indigenous-displacement-references-removed': [
            'institutional',
            'cultural',
        ],
        'executive-order-14253-restoring-truth-and-sanity': ['institutional'],
        'muir-woods-history-under-construction-exhibit-removal': [
            'institutional',
            'cultural',
        ],
        'stonewall-national-monument-lgbtq-history-altered': [
            'institutional',
            'cultural',
        ],
        'presidents-house-slavery-exhibit-removal-philadelphia': [
            'institutional',
            'cultural',
            'court-case',
        ],
        'glacier-national-park-climate-change-science-removed': ['institutional'],
        'little-bighorn-native-american-signage-removed': [
            'institutional',
            'cultural',
        ],
        'acadia-climate-indigenous-signs-removed': ['institutional', 'cultural'],
        'nmaahc-artifacts-rotated-off-display-2025': ['institutional', 'cultural'],
        'american-history-museum-impeachment-exhibit-revised': ['institutional'],
        'federal-review-nps-signs-native-climate-2026': ['institutional'],
        'zion-nps-indigenous-climate-interpretation': ['institutional', 'cultural'],
        'big-bend-nps-interpretive-content-reviewed': ['institutional'],
        'philadelphia-lawsuit-presidents-house-exhibit-2026': [
            'institutional',
            'court-case',
        ],
        'tribes-protest-grand-canyon-native-exhibits-2026': [
            'institutional',
            'cultural',
        ],
        'holc-redlining-security-maps-new-deal': ['institutional', 'cultural'],
        'chinese-exclusion-act-1882': ['institutional', 'cultural'],
        'tulsa-race-massacre-1921': ['cultural'],
    }

    for eslug, lslugs in mapping.items():
        try:
            ev = HistoricalEvent.objects.get(slug=eslug)
        except HistoricalEvent.DoesNotExist:
            continue
        ev.theme_labels.clear()
        for ls in lslugs:
            if ls in labels:
                ev.theme_labels.add(labels[ls])


def noop_reverse(apps, schema_editor):
    EventThemeLabel = apps.get_model('nomoar', 'EventThemeLabel')
    HistoricalEvent = apps.get_model('nomoar', 'HistoricalEvent')
    for ev in HistoricalEvent.objects.all():
        ev.theme_labels.clear()
    EventThemeLabel.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('nomoar', '0007_historicalevent_theme_labels'),
    ]

    operations = [
        migrations.RunPython(seed_theme_labels, noop_reverse),
    ]
