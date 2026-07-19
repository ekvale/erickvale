import json
import uuid

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .models import GemProduct, HighScore, PlayerWallet, Purchase

MAX_SCORE = 100_000_000

# Flip to a real provider key ('stripe', 'apple', 'google') once payments are
# wired up; the purchase-intent endpoint advertises this to the client.
PAYMENT_PROVIDER = Purchase.PROVIDER_NONE


def play(request):
    """Full-page version of the game."""
    return render(request, 'math_bastion/play.html')


@require_GET
def leaderboard(request):
    rows = HighScore.objects.all()[:10]
    return JsonResponse({
        'scores': [
            {
                'name': r.name,
                'score': r.score,
                'era': r.era_reached,
                'waves': r.waves_cleared,
                'victory': r.victory,
            }
            for r in rows
        ]
    })


@require_POST
def submit_score(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        name = str(data.get('name', ''))[:20].strip() or 'Anonymous'
        score = int(data.get('score', 0))
        waves = int(data.get('waves', 0))
        era = str(data.get('era', ''))[:60]
        victory = bool(data.get('victory', False))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'ok': False, 'error': 'bad payload'}, status=400)

    if not (0 <= score <= MAX_SCORE) or not (0 <= waves <= 10_000):
        return JsonResponse({'ok': False, 'error': 'out of range'}, status=400)

    HighScore.objects.create(
        name=name, score=score, waves_cleared=waves, era_reached=era, victory=victory,
    )
    return JsonResponse({'ok': True})


# ----------------------------------------------------------------------
# Store / wallet API (micropayment scaffold)
# ----------------------------------------------------------------------

def _wallet_from_request(data):
    """Fetch or create the wallet for the device key in the payload."""
    raw = str(data.get('device_key', ''))
    try:
        key = uuid.UUID(raw)
    except ValueError:
        return None
    wallet, _created = PlayerWallet.objects.get_or_create(device_key=key)
    return wallet


@require_GET
def store_catalog(request):
    products = GemProduct.objects.filter(active=True)
    return JsonResponse({
        'provider': PAYMENT_PROVIDER,
        'payments_enabled': PAYMENT_PROVIDER != Purchase.PROVIDER_NONE,
        'products': [
            {
                'sku': p.sku,
                'name': p.name,
                'description': p.description,
                'gems': p.gems,
                'bonus_gems': p.bonus_gems,
                'price_cents': p.price_cents,
            }
            for p in products
        ],
    })


@require_POST
def wallet_sync(request):
    """Return (creating if needed) the server-side wallet for a device key."""
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'bad payload'}, status=400)
    wallet = _wallet_from_request(data)
    if wallet is None:
        return JsonResponse({'ok': False, 'error': 'bad device key'}, status=400)
    return JsonResponse({'ok': True, 'gems': wallet.gems})


@require_POST
def purchase_intent(request):
    """Create a pending purchase for a gem pack.

    With no payment provider configured this records the intent and tells the
    client checkout is not yet available. When Stripe (web) or StoreKit /
    Play Billing (app) is added:
      1. create the provider checkout session here and return its id/url,
      2. add a webhook / receipt-validation view that flips the Purchase to
         COMPLETED, sets gems_granted, and credits wallet.gems atomically.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'bad payload'}, status=400)

    wallet = _wallet_from_request(data)
    if wallet is None:
        return JsonResponse({'ok': False, 'error': 'bad device key'}, status=400)

    sku = str(data.get('sku', ''))
    try:
        product = GemProduct.objects.get(sku=sku, active=True)
    except GemProduct.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'unknown product'}, status=404)

    purchase = Purchase.objects.create(
        wallet=wallet,
        product=product,
        provider=PAYMENT_PROVIDER,
        price_cents=product.price_cents,
    )

    if PAYMENT_PROVIDER == Purchase.PROVIDER_NONE:
        return JsonResponse({
            'ok': True,
            'purchase_token': str(purchase.token),
            'status': purchase.status,
            'checkout': None,
            'message': 'Payments are not enabled yet — this purchase was recorded as an intent only.',
        })

    # TODO(payments): branch per provider and return a checkout session.
    return JsonResponse({'ok': False, 'error': 'provider not implemented'}, status=501)
