import uuid

from django.db import models


class HighScore(models.Model):
    """A finished (or lost) run of Math Bastion submitted from the browser."""

    name = models.CharField(max_length=20)
    score = models.PositiveIntegerField()
    era_reached = models.CharField(max_length=60, blank=True, default='')
    waves_cleared = models.PositiveSmallIntegerField(default=0)
    victory = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-score', 'created_at']
        indexes = [models.Index(fields=['-score'])]

    def __str__(self):
        return f'{self.name} — {self.score}'


class PlayerWallet(models.Model):
    """Server-side wallet for a player, keyed by an anonymous device token.

    The browser (and later the mobile app) generates a UUID once, stores it
    locally, and sends it with wallet/store requests. When real accounts or
    App Store / Play sign-in arrive, link them here instead of replacing this.
    """

    device_key = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    gems = models.PositiveIntegerField(default=0)
    lifetime_gems_purchased = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Wallet {self.device_key} — {self.gems} gems'


class GemProduct(models.Model):
    """A purchasable gem pack. Mirror these SKUs in Stripe / App Store /
    Play Console when the payment provider is wired up."""

    sku = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=60)
    description = models.CharField(max_length=140, blank=True, default='')
    gems = models.PositiveIntegerField()
    bonus_gems = models.PositiveIntegerField(default=0)
    price_cents = models.PositiveIntegerField(help_text='USD cents; display only until a provider is configured.')
    sort_order = models.PositiveSmallIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'price_cents']

    def __str__(self):
        return f'{self.name} ({self.gems + self.bonus_gems} gems, ${self.price_cents / 100:.2f})'


class Purchase(models.Model):
    """One attempted purchase of a GemProduct.

    Flow: client POSTs an intent -> row created PENDING -> payment provider
    checkout happens client-side -> provider webhook / receipt validation
    marks it COMPLETED and credits the wallet. Until a provider is
    configured, intents stay PENDING and nothing is credited.
    """

    STATUS_PENDING = 'pending'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]

    PROVIDER_NONE = 'none'
    PROVIDER_STRIPE = 'stripe'
    PROVIDER_APPLE = 'apple'
    PROVIDER_GOOGLE = 'google'
    PROVIDER_CHOICES = [
        (PROVIDER_NONE, 'Not configured'),
        (PROVIDER_STRIPE, 'Stripe'),
        (PROVIDER_APPLE, 'Apple App Store'),
        (PROVIDER_GOOGLE, 'Google Play'),
    ]

    token = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(PlayerWallet, on_delete=models.CASCADE, related_name='purchases')
    product = models.ForeignKey(GemProduct, on_delete=models.PROTECT, related_name='purchases')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING)
    provider = models.CharField(max_length=12, choices=PROVIDER_CHOICES, default=PROVIDER_NONE)
    provider_ref = models.CharField(max_length=200, blank=True, default='',
                                    help_text='Provider-side id: Stripe session, Apple/Google transaction id.')
    price_cents = models.PositiveIntegerField()
    gems_granted = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.product.sku} · {self.status} · {self.token}'
