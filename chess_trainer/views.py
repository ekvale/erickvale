"""
Chess Opening Trainer views.
"""
import json
import re
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, DetailView
from django.views.generic.base import TemplateView
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from .models import Opening, Lesson, UserProgress, UserStats


def _get_or_create_stats(user, opening):
    stats, _ = UserStats.objects.get_or_create(user=user, opening=opening)
    return stats


def _get_progress(user, lesson):
    try:
        return UserProgress.objects.get(user=user, lesson=lesson)
    except UserProgress.DoesNotExist:
        return None


def _update_daily_streak(stats):
    """Update streak based on last_practiced date."""
    if not stats.last_practiced:
        stats.streak = 1
    else:
        today = timezone.now().date()
        delta = (today - stats.last_practiced).days
        if delta == 0:
            pass  # Same day, no change
        elif delta == 1:
            stats.streak += 1
        else:
            stats.streak = 1
    stats.save()


class DashboardView(TemplateView):
    """Shows all 4 openings, mastery % per opening, daily streak, next recommended lesson."""
    template_name = 'chess_trainer/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        openings = Opening.objects.prefetch_related('lessons').all()
        ctx['openings'] = openings

        if self.request.user.is_authenticated:
            user = self.request.user
            stats_list = []
            total_mastery = 0
            for op in openings:
                stats = _get_or_create_stats(user, op)
                stats_list.append({'opening': op, 'stats': stats})
                total_mastery += stats.mastery_pct

            ctx['stats_list'] = stats_list
            ctx['avg_mastery'] = total_mastery / len(openings) if openings else 0

            # Daily streak (max across openings)
            ctx['streak'] = max((s['stats'].streak for s in stats_list), default=0)

            # Next recommended: lessons due for review, or first incomplete lesson
            today = timezone.now().date()
            due_openings = UserStats.objects.filter(
                user=user,
                next_review_date__lte=today,
                next_review_date__isnull=False
            ).exclude(mastery_pct=100).select_related('opening')

            next_lesson = None
            if due_openings.exists():
                # Pick first opening with review due, get its first lesson
                for us in due_openings[:1]:
                    first_lesson = us.opening.lessons.order_by('order').first()
                    if first_lesson:
                        next_lesson = first_lesson
                        break

            if not next_lesson:
                # Find first incomplete lesson across all openings
                completed_ids = UserProgress.objects.filter(
                    user=user, completed=True
                ).values_list('lesson_id', flat=True)
                next_lesson = Lesson.objects.exclude(
                    id__in=completed_ids
                ).order_by('opening', 'order').first()

            ctx['next_lesson'] = next_lesson
        else:
            ctx['stats_list'] = [{'opening': o, 'stats': None} for o in openings]
            ctx['avg_mastery'] = 0
            ctx['streak'] = 0
            ctx['next_lesson'] = openings.first().lessons.order_by('order').first() if openings.exists() else None

        return ctx


class OpeningDetailView(DetailView):
    """Overview of one opening with all lessons listed and progress indicators."""
    model = Opening
    template_name = 'chess_trainer/opening_detail.html'
    context_object_name = 'opening'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        lessons = self.object.lessons.order_by('order')
        ctx['lessons'] = lessons

        if self.request.user.is_authenticated:
            user = self.request.user
            stats = _get_or_create_stats(user, self.object)
            ctx['stats'] = stats
            progress_map = {lp.lesson_id: lp for lp in UserProgress.objects.filter(user=user, lesson__in=lessons)}
            # Attach progress to each lesson for template
            lesson_list = []
            for l in lessons:
                prog = progress_map.get(l.id)
                lesson_list.append({'lesson': l, 'progress': prog})
            ctx['lesson_list'] = lesson_list
        else:
            ctx['stats'] = None
            ctx['lesson_list'] = [{'lesson': l, 'progress': None} for l in lessons]

        return ctx


class LessonView(DetailView):
    """Renders a single lesson (concept, drill, or quiz) with chess board."""
    model = Lesson
    template_name = 'chess_trainer/lesson_concept.html'  # Default, overridden per type
    context_object_name = 'lesson'

    def get_template_names(self):
        t = self.object.lesson_type
        if t == 'drill':
            return ['chess_trainer/lesson_drill.html']
        if t == 'quiz':
            return ['chess_trainer/lesson_quiz.html']
        return ['chess_trainer/lesson_concept.html']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['opening'] = self.object.opening
        content = self.object.content or {}
        ctx['content'] = content
        ctx['user_authenticated'] = self.request.user.is_authenticated
        # For drills: flatten expected_moves if it's opening move pairs
        if self.object.lesson_type == 'drill':
            expected = content.get('expected_moves')
            if not expected and self.object.opening.move_sequence:
                seq = self.object.opening.move_sequence
                flat = []
                for pair in seq:
                    if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                        if pair[0]:
                            flat.append(pair[0])
                        if pair[1]:
                            flat.append(pair[1])
                    elif isinstance(pair, str):
                        flat.append(pair)
                ctx['expected_moves_json'] = json.dumps(flat)
            else:
                ctx['expected_moves_json'] = json.dumps(expected if isinstance(expected, list) else [])
        ctx['progress'] = _get_progress(self.request.user, self.object) if self.request.user.is_authenticated else None
        ctx['user_authenticated'] = self.request.user.is_authenticated
        return ctx


class QuizView(DetailView):
    """Presents a position and 4 multiple choice moves."""
    model = Lesson
    template_name = 'chess_trainer/lesson_quiz.html'
    context_object_name = 'lesson'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['opening'] = self.object.opening
        ctx['content'] = self.object.content or {}
        ctx['progress'] = _get_progress(self.request.user, self.object) if self.request.user.is_authenticated else None
        ctx['user_authenticated'] = self.request.user.is_authenticated
        return ctx


class DrillView(DetailView):
    """User inputs correct move order from scratch (no hints)."""
    model = Lesson
    template_name = 'chess_trainer/lesson_drill.html'
    context_object_name = 'lesson'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['opening'] = self.object.opening
        content = self.object.content or {}
        ctx['content'] = content
        expected = content.get('expected_moves')
        if not expected and self.object.opening.move_sequence:
            seq = self.object.opening.move_sequence
            flat = []
            for pair in seq:
                if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                    if pair[0]:
                        flat.append(pair[0])
                    if pair[1]:
                        flat.append(pair[1])
                elif isinstance(pair, str):
                    flat.append(pair)
            ctx['expected_moves_json'] = json.dumps(flat)
        else:
            ctx['expected_moves_json'] = json.dumps(expected if isinstance(expected, list) else [])
        ctx['progress'] = _get_progress(self.request.user, self.object) if self.request.user.is_authenticated else None
        ctx['user_authenticated'] = self.request.user.is_authenticated
        return ctx


class LessonSubmitView(View):
    """POST endpoint to validate move/answer and update UserProgress + UserStats."""

    def post(self, request, pk):
        lesson = get_object_or_404(Lesson, pk=pk)
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'error': 'Login required'}, status=401)

        try:
            data = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            data = request.POST.dict()

        action = data.get('action', 'validate')
        user = request.user

        if action == 'mark_read':
            # Concept lesson: just mark completed
            prog, _ = UserProgress.objects.get_or_create(user=user, lesson=lesson)
            prog.completed = True
            prog.last_attempted = timezone.now()
            prog.save()
            stats = _get_or_create_stats(user, lesson.opening)
            _update_daily_streak(stats)
            return JsonResponse({'success': True, 'completed': True})

        if action == 'quiz':
            # Quiz: validate selected move (normalize: strip move numbers like "5.")
            selected = re.sub(r'^\d+\.', '', data.get('selected_move', '').strip()).lower()
            correct_move = re.sub(r'^\d+\.', '', str((lesson.content or {}).get('correct_move', '')).strip()).lower()
            correct = selected == correct_move
            return self._record_result(user, lesson, correct, 100 if correct else 0)

        if action == 'drill':
            # Drill: validate move sequence
            moves = data.get('moves', [])
            if isinstance(moves, str):
                moves = [m.strip() for m in moves.replace(',', ' ').split() if m.strip()]
            correct_sequence = _get_drill_expected_moves(lesson)
            correct = _validate_move_sequence(moves, correct_sequence, lesson.opening.side)
            score = 100 if correct else 0
            return self._record_result(user, lesson, correct, score)

        return JsonResponse({'success': False, 'error': 'Unknown action'}, status=400)

    def _record_result(self, user, lesson, correct, score):
        prog, _ = UserProgress.objects.get_or_create(user=user, lesson=lesson)
        prog.attempts += 1
        prog.last_attempted = timezone.now()
        prog.completed = prog.completed or correct
        if correct and score > prog.score:
            prog.score = score
        prog.save()

        stats = _get_or_create_stats(user, lesson.opening)
        stats.update_spaced_repetition(correct)
        _update_daily_streak(stats)

        return JsonResponse({
            'success': True,
            'correct': correct,
            'score': prog.score,
            'mastery_pct': stats.mastery_pct,
        })


def _get_drill_expected_moves(lesson):
    """Return list of expected moves for a drill from lesson content or opening."""
    content = lesson.content or {}
    if 'expected_moves' in content:
        return content['expected_moves']
    # Fall back to opening move sequence
    opening = lesson.opening
    seq = opening.move_sequence or []
    flat = []
    for pair in seq:
        if isinstance(pair, list):
            w, b = pair[0] if len(pair) > 0 else None, pair[1] if len(pair) > 1 else None
            if opening.side == 'white' and w:
                flat.append(w)
            if opening.side == 'black' and b:
                flat.append(b)
        elif isinstance(pair, str):
            flat.append(pair)
    return flat


def _validate_move_sequence(actual, expected, side):
    """Validate that actual move list matches expected. Handles SAN normalization."""
    if not expected:
        return False
    # Normalize: lowercase, no dots, strip; treat O-O and 0-0 as equivalent
    def norm(s):
        s = str(s).strip().replace('.', '')
        s_lower = s.lower()
        if re.match(r'^[o0]-[o0](-[o0])?$', s_lower):
            s_lower = s_lower.replace('o', '0')
        return s_lower
    exp_norm = [norm(m) for m in expected]
    act_norm = [norm(m) for m in actual]
    if len(act_norm) != len(exp_norm):
        return False
    for a, e in zip(act_norm, exp_norm):
        if a != e:
            return False
    return True
