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
    
    # Session or GET params for revealed clues count and active filters
    session_key = f'detective_case_{pk}'
    session_data = request.session.get(session_key, {})
    clues_revealed = session_data.get('clues_revealed', 0)
    current_filters = session_data.get('filters', {})
    game_over = session_data.get('game_over', False)
    
    # Reveal one more clue on demand
    if request.GET.get('reveal') == 'next' and clues_revealed < clues.count():
        clues_revealed += 1
        # Merge new clue's filter_hints into current_filters
        if clues_revealed > 0:
            clue = clues[clues_revealed - 1]
            for k, v in (clue.filter_hints or {}).items():
                if v and (k not in current_filters or current_filters[k] != v):
                    current_filters[k] = v
        session_data['clues_revealed'] = clues_revealed
        session_data['filters'] = current_filters
        request.session[session_key] = session_data
        request.session.modified = True
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
    
    visible_clues = list(clues[:clues_revealed])
    
    last_correct = session_data.get('correct')
    
    context = {
        'case': case,
        'clues': visible_clues,
        'clues_total': clues.count(),
        'clues_revealed': clues_revealed,
        'can_reveal_more': clues_revealed < clues.count(),
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
        'gender', 'age_range', 'hair_color', 'eye_color', 'skin_tone',
        'build', 'height_range', 'accent_region', 'vehicle_type', 'vehicle_color',
    ]
    for field in filter_fields:
        val = request.POST.get(field, '').strip()
        if val:
            current_filters[field] = val
        elif field in current_filters:
            del current_filters[field]
    
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
        'build', 'height_range', 'accent_region', 'vehicle_type', 'vehicle_color',
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
