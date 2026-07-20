from django.db import migrations

GEM_PACKS = [
    dict(sku='gems-pouch', name='Pouch of Gems', description='A handful of insight.',
         gems=100, bonus_gems=0, price_cents=199, sort_order=1),
    dict(sku='gems-satchel', name='Satchel of Gems', description='Most popular with scribes.',
         gems=550, bonus_gems=50, price_cents=499, sort_order=2),
    dict(sku='gems-chest', name='Chest of Gems', description='Enough to fund a small academy.',
         gems=1200, bonus_gems=200, price_cents=999, sort_order=3),
    dict(sku='gems-vault', name='House of Wisdom Vault', description='Best value. Baghdad approved.',
         gems=2600, bonus_gems=600, price_cents=1999, sort_order=4),
]


def seed(apps, schema_editor):
    GemProduct = apps.get_model('math_bastion', 'GemProduct')
    for pack in GEM_PACKS:
        GemProduct.objects.update_or_create(sku=pack['sku'], defaults=pack)


def unseed(apps, schema_editor):
    GemProduct = apps.get_model('math_bastion', 'GemProduct')
    GemProduct.objects.filter(sku__in=[p['sku'] for p in GEM_PACKS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('math_bastion', '0002_gemproduct_playerwallet_purchase'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
