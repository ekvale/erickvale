import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .models import HighScore

MAX_SCORE = 10_000_000


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

    if not (0 <= score <= MAX_SCORE) or not (0 <= waves <= 200):
        return JsonResponse({'ok': False, 'error': 'out of range'}, status=400)

    HighScore.objects.create(
        name=name, score=score, waves_cleared=waves, era_reached=era, victory=victory,
    )
    return JsonResponse({'ok': True})
