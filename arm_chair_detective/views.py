"""
Views for Arm Chair Detective - case list, case play, filtering, and guessing.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from .models import Case, Suspect, Clue


def case_list(request):
    """List all published cases."""
    cases = Case.objects.filter(is_published=True).select_related('perpetrator')
    difficulty = request.GET.get('difficulty', '')
    if difficulty:
        cases = cases.filter(difficulty=difficulty)
    context = {
        'cases': cases,
        'difficulty_filter': difficulty,
    }
    return render(request, 'arm_chair_detective/case_list.html', context)


def case_play(request, pk):
    """Main game view: case briefing, clues, suspect filter, and guess."""
    case = get_object_or_404(Case.objects.select_related('perpetrator').prefetch_related('clues'), pk=pk)
    clues = case.clues.all().order_by('order')
    
    # Session: revealed clues count, filters, case time (for timeline pressure)
    session_key = f'detective_case_{pk}'
    session_data = request.session.get(session_key, {})
    clues_revealed = session_data.get('clues_revealed', 0)
    current_filters = session_data.get('filters', {})
    game_over = session_data.get('game_over', False)
    case_hours_elapsed = session_data.get('case_hours_elapsed', 0)
    
    # Advance time (timeline pressure)
    if request.GET.get('advance') == 'time':
        case_hours_elapsed = min(case_hours_elapsed + 12, 72)  # cap at 72h
        session_data['case_hours_elapsed'] = case_hours_elapsed
        request.session[session_key] = session_data
        request.session.modified = True
        messages.info(request, f'Time advanced. Case timeline: {case_hours_elapsed} hours since incident.')
        return redirect('arm_chair_detective:case_play', pk=pk)
    
    # Reveal one more clue on demand (filters are NOT auto-applied; user applies them manually)
    if request.GET.get('reveal') == 'next' and clues_revealed < clues.count():
        ordered_clues = list(clues)
        next_clue = ordered_clues[clues_revealed] if clues_revealed < len(ordered_clues) else None
        if next_clue and next_clue.unlock_after_hours is not None and case_hours_elapsed < next_clue.unlock_after_hours:
            hours_needed = next_clue.unlock_after_hours - case_hours_elapsed
            messages.warning(request, f'This clue is not yet available. Advance time by {hours_needed}+ hours.')
        else:
            clues_revealed += 1
            session_data['clues_revealed'] = clues_revealed
            request.session[session_key] = session_data
            request.session.modified = True
            messages.success(request, 'New clue revealed.')
        return redirect('arm_chair_detective:case_play', pk=pk)
    
    # Build suspect queryset with filters
    suspects_qs = Suspect.objects.all()
    for field, value in current_filters.items():
        if value and hasattr(Suspect, field):
            suspects_qs = suspects_qs.filter(**{field: value})
    
    suspect_count = suspects_qs.count()
    
    # Pagination for suspect list
    paginator = Paginator(suspects_qs, 50)
    page = request.GET.get('page', 1)
    page_obj = paginator.get_page(page)
    
    ordered_clues = list(clues)
    visible_clues = ordered_clues[:clues_revealed]
    next_clue = ordered_clues[clues_revealed] if clues_revealed < len(ordered_clues) else None
    next_clue_blocked = (
        next_clue is not None
        and next_clue.unlock_after_hours is not None
        and case_hours_elapsed < next_clue.unlock_after_hours
    )
    next_clue_hours_needed = (
        (next_clue.unlock_after_hours - case_hours_elapsed)
        if next_clue_blocked and next_clue
        else 0
    )
    
    last_correct = session_data.get('correct')
    
    context = {
        'case': case,
        'clues': visible_clues,
        'clues_total': clues.count(),
        'clues_revealed': clues_revealed,
        'can_reveal_more': clues_revealed < clues.count(),
        'next_clue_blocked': next_clue_blocked,
        'next_clue_hours_needed': next_clue_hours_needed,
        'case_hours_elapsed': case_hours_elapsed,
        'page_obj': page_obj,
        'suspect_count': suspect_count,
        'current_filters': current_filters,
        'game_over': game_over,
        'last_correct': last_correct,
    }
    return render(request, 'arm_chair_detective/case_play.html', context)


@require_POST
def apply_filter(request, pk):
    """Apply or update filters via POST (e.g. from a filter form)."""
    case = get_object_or_404(Case, pk=pk)
    session_key = f'detective_case_{pk}'
    session_data = request.session.get(session_key, {})
    current_filters = dict(session_data.get('filters', {}))
    
    filter_fields = [
        'gender', 'hair_color', 'eye_color', 'skin_tone',
        'build', 'accent_region', 'vehicle_type', 'vehicle_color', 'occupation',
    ]
    for field in filter_fields:
        val = request.POST.get(field, '').strip()
        if val:
            current_filters[field] = val
        elif field in current_filters:
            del current_filters[field]
    
    # Map age slider (0=any, 1=teens..6=sixties_plus)
    age_map = ['', 'teens', 'twenties', 'thirties', 'forties', 'fifties', 'sixties_plus']
    age_slider = request.POST.get('age_slider', '')
    if age_slider.isdigit():
        idx = int(age_slider)
        if 0 < idx < len(age_map):
            current_filters['age_range'] = age_map[idx]
        elif idx == 0 and 'age_range' in current_filters:
            del current_filters['age_range']
    
    # Map height slider (0=any, 1=short..4=very_tall)
    height_map = ['', 'short', 'medium', 'tall', 'very_tall']
    height_slider = request.POST.get('height_slider', '')
    if height_slider.isdigit():
        idx = int(height_slider)
        if 0 < idx < len(height_map):
            current_filters['height_range'] = height_map[idx]
        elif idx == 0 and 'height_range' in current_filters:
            del current_filters['height_range']
    
    session_data['filters'] = current_filters
    request.session[session_key] = session_data
    request.session.modified = True
    messages.info(request, 'Filters applied.')
    return redirect('arm_chair_detective:case_play', pk=pk)


@require_POST
def submit_guess(request, pk):
    """User submits a suspect as their guess."""
    case = get_object_or_404(Case.objects.select_related('perpetrator'), pk=pk)
    suspect_id = request.POST.get('suspect_id')
    session_key = f'detective_case_{pk}'
    
    if not suspect_id:
        messages.error(request, 'Please select a suspect.')
        return redirect('arm_chair_detective:case_play', pk=pk)
    
    try:
        suspect = Suspect.objects.get(pk=suspect_id)
    except Suspect.DoesNotExist:
        messages.error(request, 'Invalid suspect.')
        return redirect('arm_chair_detective:case_play', pk=pk)
    
    correct = (suspect.pk == case.perpetrator_id)
    session_data = request.session.get(session_key, {})
    session_data['game_over'] = True
    session_data['last_guess'] = suspect_id
    session_data['correct'] = correct
    request.session[session_key] = session_data
    request.session.modified = True
    
    if correct:
        messages.success(request, f'Correct! {suspect.full_name} is the perpetrator. Case closed.')
    else:
        messages.error(request, f'Incorrect. {suspect.full_name} is not the perpetrator. Keep investigating.')
    
    return redirect('arm_chair_detective:case_play', pk=pk)


def advance_time(request, pk):
    """Advance case timeline by 12 hours (for unlocking time-gated clues)."""
    case = get_object_or_404(Case, pk=pk)
    session_key = f'detective_case_{pk}'
    session_data = request.session.get(session_key, {})
    case_hours_elapsed = session_data.get('case_hours_elapsed', 0)
    case_hours_elapsed = min(case_hours_elapsed + 12, 72)
    session_data['case_hours_elapsed'] = case_hours_elapsed
    request.session[session_key] = session_data
    request.session.modified = True
    messages.info(request, f'Time advanced. Case timeline: {case_hours_elapsed} hours since incident.')
    return redirect('arm_chair_detective:case_play', pk=pk)


def reset_case(request, pk):
    """Reset progress for a case (start over)."""
    session_key = f'detective_case_{pk}'
    if session_key in request.session:
        del request.session[session_key]
        request.session.modified = True
    messages.info(request, 'Case progress reset. Start fresh!')
    return redirect('arm_chair_detective:case_play', pk=pk)


@require_GET
def suspect_count_api(request, pk):
    """API: return current suspect count for given filters (for dynamic filter UI)."""
    case = get_object_or_404(Case, pk=pk)
    session_key = f'detective_case_{pk}'
    session_data = request.session.get(session_key, {})
    filters = dict(session_data.get('filters', {}))
    
    # Merge any GET params as additional filters
    filter_fields = [
        'gender', 'age_range', 'hair_color', 'eye_color', 'skin_tone',
        'build', 'height_range', 'accent_region', 'vehicle_type', 'vehicle_color', 'occupation',
    ]
    for field in filter_fields:
        val = request.GET.get(field, '').strip()
        if val:
            filters[field] = val
    
    qs = Suspect.objects.all()
    for field, value in filters.items():
        if value and hasattr(Suspect, field):
            qs = qs.filter(**{field: value})
    
    return JsonResponse({'count': qs.count()})
