import json
import random
import uuid
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.db.models import Q
from .models import Scenario, GameSession, GameRound, PERSONALITY_TYPE_CHOICES, TELL_CATEGORY_CHOICES


def game_home(request):
    """Display game home page with instructions."""
    context = {
        'personality_types': PERSONALITY_TYPE_CHOICES,
        'tell_categories': TELL_CATEGORY_CHOICES,
    }
    return render(request, 'personality_type_game/home.html', context)


@csrf_exempt
def start_game(request):
    """Start a new game session."""
    if request.method == 'POST':
        data = json.loads(request.body)
        difficulty = data.get('difficulty', 'medium')
        training_mode = data.get('training_mode', False)
        
        # Create new session
        session_id = str(uuid.uuid4())
        session = GameSession.objects.create(
            session_id=session_id,
            difficulty=difficulty,
            training_mode=training_mode
        )
        
        return JsonResponse({
            'session_id': session_id,
            'success': True
        })
    
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


@csrf_exempt
def get_scenario(request, session_id):
    """Get a random scenario for the current round, avoiding recent ones."""
    session = get_object_or_404(GameSession, session_id=session_id)
    
    # Get already played scenario IDs
    played_ids = list(GameRound.objects.filter(session=session)
                     .values_list('scenario_id', flat=True))
    
    # Get last 2 scenarios to avoid repeating
    recent_rounds = GameRound.objects.filter(session=session).order_by('-round_number')[:2]
    recent_ids = [r.scenario_id for r in recent_rounds]
    
    # Filter scenarios by difficulty
    scenarios = Scenario.objects.filter(difficulty=session.difficulty)
    
    # Exclude recent scenarios
    if recent_ids:
        scenarios = scenarios.exclude(id__in=recent_ids)
    
    if not scenarios.exists():
        # If we've run out of scenarios, allow repeats but still exclude last 2
        scenarios = Scenario.objects.filter(difficulty=session.difficulty)
        if recent_ids:
            scenarios = scenarios.exclude(id__in=recent_ids)
    
    if not scenarios.exists():
        # Last resort: allow any scenario
        scenarios = Scenario.objects.filter(difficulty=session.difficulty)
    
    scenario = random.choice(scenarios)
    
    # Get round number
    round_number = GameRound.objects.filter(session=session).count() + 1
    
    # Create round record (not yet answered)
    round_obj = GameRound.objects.create(
        session=session,
        scenario=scenario,
        round_number=round_number
    )
    
    return JsonResponse({
        'round_id': round_obj.id,
        'round_number': round_number,
        'scenario': {
            'id': scenario.id,
            'title': scenario.scenario_title,
            'transcript': scenario.transcript,
            'response_choices': scenario.response_choices,
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def submit_answer(request, session_id, round_id):
    """Submit answer for a round and get feedback."""
    session = get_object_or_404(GameSession, session_id=session_id)
    round_obj = get_object_or_404(GameRound, id=round_id, session=session)
    
    if round_obj.player_type_guess is not None:
        # Already answered
        return JsonResponse({'error': 'Round already answered'}, status=400)
    
    data = json.loads(request.body)
    round_obj.player_type_guess = data.get('type_guess')
    round_obj.player_response_choice = data.get('response_choice')
    round_obj.player_tell_category = data.get('tell_category')
    round_obj.hint_used = data.get('hint_used', False)
    
    # Calculate score
    points = round_obj.calculate_score()
    round_obj.save()
    
    # Update session stats
    session.total_score += points
    session.total_rounds += 1
    
    if round_obj.type_correct and round_obj.response_correct:
        session.current_streak += 1
        if session.current_streak > session.best_streak:
            session.best_streak = session.current_streak
    else:
        session.current_streak = 0
    
    session.save()
    
    # Prepare feedback
    scenario = round_obj.scenario
    feedback = {
        'points_earned': points,
        'type_correct': round_obj.type_correct,
        'response_correct': round_obj.response_correct,
        'tell_correct': round_obj.tell_correct,
        'correct_type': scenario.correct_type,
        'correct_type_display': scenario.get_correct_type_display(),
        'correct_response': scenario.correct_response,
        'correct_tell_category': scenario.tell_category,
        'correct_tell_category_display': scenario.get_tell_category_display(),
        'tell_explanation': scenario.tell_explanation,
        'response_explanation': scenario.response_explanation,
        'session_stats': {
            'total_score': session.total_score,
            'total_rounds': session.total_rounds,
            'current_streak': session.current_streak,
            'best_streak': session.best_streak,
            'accuracy': session.get_accuracy(),
        }
    }
    
    return JsonResponse(feedback)


@csrf_exempt
def get_hint(request, session_id, round_id):
    """Get hint for tell category (costs 1 point in training mode)."""
    session = get_object_or_404(GameSession, session_id=session_id)
    round_obj = get_object_or_404(GameRound, id=round_id, session=session)
    
    if round_obj.player_type_guess is not None:
        return JsonResponse({'error': 'Round already answered'}, status=400)
    
    scenario = round_obj.scenario
    
    return JsonResponse({
        'tell_category': scenario.tell_category,
        'tell_category_display': scenario.get_tell_category_display(),
        'costs_point': session.training_mode,
    })


def game_summary(request, session_id):
    """Display final game summary with review of missed questions."""
    session = get_object_or_404(GameSession, session_id=session_id)
    rounds = GameRound.objects.filter(session=session).order_by('round_number')
    
    missed_rounds = [r for r in rounds if not (r.type_correct and r.response_correct)]
    
    context = {
        'session': session,
        'total_rounds': rounds.count(),
        'missed_rounds': missed_rounds,
        'type_accuracy': session.get_type_accuracy(),
    }
    
    # Mark session as completed
    if not session.completed:
        session.completed = True
        session.save()
    
    return render(request, 'personality_type_game/summary.html', context)


@ensure_csrf_cookie
def play_game(request, session_id=None):
    """Main game play page."""
    if session_id:
        session = get_object_or_404(GameSession, session_id=session_id)
    else:
        session = None
    
    context = {
        'session': session,
        'personality_types': PERSONALITY_TYPE_CHOICES,
        'tell_categories': TELL_CATEGORY_CHOICES,
    }
    
    return render(request, 'personality_type_game/play.html', context)
