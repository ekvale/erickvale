from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Count, Max, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    CommentForm,
    ContactForm,
    DocumentUploadForm,
    EventForm,
    ProjectForm,
    ProjectMembershipForm,
    TaskForm,
)
from .models import (
    Comment,
    Contact,
    ContactType,
    Document,
    Event,
    EventType,
    MembershipRole,
    Notification,
    Priority,
    Project,
    ProjectMembership,
    ProjectStatus,
    Task,
    TaskStatus,
)

User = get_user_model()


def _accessible_projects_qs(user):
    return Project.objects.filter(Q(owner=user) | Q(memberships__user=user)).distinct()


def _get_project_for_user(user, pk):
    return get_object_or_404(_accessible_projects_qs(user), pk=pk)


def _set_task_actor(task, user):
    task._actor = user
    task._actor_id = user.id


def _event_type_color(event_type):
    return {
        EventType.MEETING: '#003865',
        EventType.DEADLINE: '#c2410c',
        EventType.MILESTONE: '#008EAA',
        EventType.REVIEW: '#7c3aed',
        EventType.OTHER: '#64748b',
    }.get(event_type, '#64748b')


def _accessible_events_qs(user):
    projects = _accessible_projects_qs(user)
    return (
        Event.objects.filter(
            Q(project__in=projects)
            | Q(attendees=user)
            | Q(created_by=user)
            | Q(project__isnull=True, created_by=user)
        )
        .select_related('project', 'created_by')
        .prefetch_related('attendees')
        .distinct()
    )


@login_required
def project_list(request):
    qs = _accessible_projects_qs(request.user).order_by('-updated_at')
    status = request.GET.get('status', '').strip()
    if status:
        qs = qs.filter(status=status)
    today = timezone.now().date()
    qs = qs.prefetch_related('memberships__user').annotate(
        open_task_count=Count(
            'tasks',
            filter=~Q(tasks__status=TaskStatus.DONE),
            distinct=True,
        ),
        overdue_task_count=Count(
            'tasks',
            filter=~Q(tasks__status=TaskStatus.DONE)
            & Q(tasks__due_date__isnull=False)
            & Q(tasks__due_date__lt=today),
            distinct=True,
        ),
    )
    return render(
        request,
        'projects/project_list.html',
        {
            'projects': qs,
            'status_filter': status,
            'status_choices': ProjectStatus.choices,
        },
    )


@login_required
def project_create(request):
    form = ProjectForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        ProjectMembership.objects.get_or_create(
            project=project,
            user=request.user,
            defaults={'role': MembershipRole.OWNER},
        )
        messages.success(request, 'Project created.')
        return redirect('projects:project_detail', pk=project.pk)
    return render(request, 'projects/project_form.html', {'form': form, 'is_create': True})


@login_required
def project_edit(request, pk):
    project = _get_project_for_user(request.user, pk)
    form = ProjectForm(request.POST or None, instance=project)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Project updated.')
        return redirect('projects:project_detail', pk=project.pk)
    return render(
        request,
        'projects/project_form.html',
        {'form': form, 'project': project, 'is_create': False},
    )


@login_required
def project_detail(request, pk):
    project = _get_project_for_user(request.user, pk)
    recent_comments = (
        Comment.objects.filter(task__project=project)
        .select_related('author', 'task')
        .order_by('-created_at')[:10]
    )
    recent_task_updates = (
        Task.objects.filter(project=project)
        .order_by('-updated_at')[:10]
        .select_related('created_by')
    )
    open_tasks = (
        Task.objects.filter(project=project)
        .exclude(status=TaskStatus.DONE)
        .order_by('status', 'order', 'pk')
    )
    open_by_status = {s: [] for s, _ in TaskStatus.choices}
    for t in open_tasks:
        open_by_status.setdefault(t.status, []).append(t)
    open_columns = [
        {'status': s, 'label': lbl, 'tasks': open_by_status.get(s, [])}
        for s, lbl in TaskStatus.choices
    ]
    upcoming_events = (
        Event.objects.filter(project=project, start_datetime__gte=timezone.now())
        .order_by('start_datetime')[:8]
    )
    recent_documents = Document.objects.filter(project=project).select_related('uploaded_by')[:8]
    members = project.memberships.select_related('user').order_by('joined_at')
    return render(
        request,
        'projects/project_detail.html',
        {
            'project': project,
            'recent_comments': recent_comments,
            'recent_task_updates': recent_task_updates,
            'open_by_status': open_by_status,
            'open_columns': open_columns,
            'upcoming_events': upcoming_events,
            'recent_documents': recent_documents,
            'members': members,
        },
    )


@login_required
def task_list(request, pk):
    project = _get_project_for_user(request.user, pk)
    tasks = (
        Task.objects.filter(project=project, parent_task__isnull=True)
        .select_related('created_by')
        .prefetch_related('assignees')
        .order_by('order', 'pk')
    )
    assignee_filter = request.GET.get('assignee', '').strip()
    priority_filter = request.GET.get('priority', '').strip()
    if assignee_filter.isdigit():
        tasks = tasks.filter(assignees__id=int(assignee_filter))
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    columns = {status: [] for status, _label in TaskStatus.choices}
    today = timezone.now().date()
    for task in tasks:
        columns.setdefault(task.status, []).append(task)
    column_list = [
        {'status': s, 'label': lbl, 'tasks': columns.get(s, [])}
        for s, lbl in TaskStatus.choices
    ]
    assignee_choices = []
    uids = set()
    if project.owner_id:
        assignee_choices.append(project.owner)
        uids.add(project.owner_id)
    for m in project.memberships.select_related('user'):
        if m.user_id not in uids:
            assignee_choices.append(m.user)
            uids.add(m.user_id)
    return render(
        request,
        'projects/task_list.html',
        {
            'project': project,
            'column_list': column_list,
            'today': today,
            'assignee_filter': assignee_filter,
            'priority_filter': priority_filter,
            'assignee_choices': assignee_choices,
        },
    )


@login_required
def task_create(request, pk):
    project = _get_project_for_user(request.user, pk)
    form = TaskForm(request.POST or None, project=project)
    if request.method == 'POST' and form.is_valid():
        task = form.save(commit=False)
        task.project = project
        task.created_by = request.user
        if task.order == 0:
            mx = (
                Task.objects.filter(project=project, status=task.status).aggregate(
                    m=Max('order')
                )['m']
            )
            task.order = (mx or 0) + 1
        _set_task_actor(task, request.user)
        task.save()
        form.save_m2m()
        messages.success(request, 'Task created.')
        return redirect('projects:task_detail', pk=project.pk, task_pk=task.pk)
    return render(
        request,
        'projects/task_form.html',
        {'form': form, 'project': project, 'task': None},
    )


@login_required
def task_edit(request, pk, task_pk):
    project = _get_project_for_user(request.user, pk)
    task = get_object_or_404(Task, pk=task_pk, project=project)
    form = TaskForm(
        request.POST or None,
        instance=task,
        project=project,
        task_instance=task,
    )
    if request.method == 'POST' and form.is_valid():
        t = form.save(commit=False)
        _set_task_actor(t, request.user)
        t.save()
        form.save_m2m()
        messages.success(request, 'Task saved.')
        return redirect('projects:task_detail', pk=project.pk, task_pk=task.pk)
    return render(
        request,
        'projects/task_form.html',
        {'form': form, 'project': project, 'task': task},
    )


@login_required
def task_detail(request, pk, task_pk):
    project = _get_project_for_user(request.user, pk)
    task = get_object_or_404(
        Task.objects.prefetch_related('assignees'),
        pk=task_pk,
        project=project,
    )
    subtasks = task.subtasks.prefetch_related('assignees').all().order_by('order', 'pk')
    done_sub = subtasks.filter(status=TaskStatus.DONE).count()
    total_sub = subtasks.count()
    comments = task.comments.select_related('author').order_by('created_at')
    comment_form = CommentForm(request.POST or None)
    if request.method == 'POST' and comment_form.is_valid():
        c = comment_form.save(commit=False)
        c.task = task
        c.author = request.user
        c.save()
        messages.success(request, 'Comment added.')
        return redirect('projects:task_detail', pk=project.pk, task_pk=task.pk)
    docs = Document.objects.filter(task=task).select_related('uploaded_by')
    return render(
        request,
        'projects/task_detail.html',
        {
            'project': project,
            'task': task,
            'subtasks': subtasks,
            'done_sub': done_sub,
            'total_sub': total_sub,
            'comments': comments,
            'comment_form': comment_form,
            'documents': docs,
        },
    )


@login_required
def document_list(request, pk):
    project = _get_project_for_user(request.user, pk)
    documents = Document.objects.filter(project=project).select_related('uploaded_by')
    return render(
        request,
        'projects/document_list.html',
        {'project': project, 'documents': documents},
    )


@login_required
def document_upload(request, pk):
    project = _get_project_for_user(request.user, pk)
    form = DocumentUploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        doc = form.save(commit=False)
        doc.project = project
        doc.uploaded_by = request.user
        doc.full_clean()
        doc.save()
        messages.success(request, 'Document uploaded.')
        return redirect('projects:document_list', pk=project.pk)
    return render(
        request,
        'projects/document_upload_form.html',
        {'project': project, 'form': form},
    )


@login_required
def member_list(request, pk):
    project = _get_project_for_user(request.user, pk)
    memberships = project.memberships.select_related('user').order_by('joined_at')
    form = ProjectMembershipForm(request.POST or None, project=project)
    if request.method == 'POST' and form.is_valid():
        m = form.save(commit=False)
        m.project = project
        try:
            m.save()
        except IntegrityError:
            messages.error(request, 'That user is already a member of this project.')
        else:
            messages.success(request, 'Member added.')
        return redirect('projects:member_list', pk=project.pk)
    return render(
        request,
        'projects/member_list.html',
        {'project': project, 'memberships': memberships, 'form': form},
    )


@login_required
def contact_list(request):
    qs = Contact.objects.all().select_related('added_by').prefetch_related('projects').order_by(
        'last_name', 'first_name'
    )
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(organization__icontains=q)
        )
    ct = request.GET.get('contact_type', '').strip()
    if ct:
        qs = qs.filter(contact_type=ct)
    return render(
        request,
        'projects/contact_list.html',
        {
            'contacts': qs,
            'q': q,
            'contact_type': ct,
            'contact_type_choices': ContactType.choices,
        },
    )


@login_required
def contact_create(request):
    accessible = _accessible_projects_qs(request.user)
    form = ContactForm(
        request.POST or None,
        accessible_projects_queryset=accessible,
    )
    if request.method == 'POST' and form.is_valid():
        c = form.save(commit=False)
        c.added_by = request.user
        c.save()
        form.save_m2m()
        messages.success(request, 'Contact saved.')
        return redirect('projects:contact_detail', pk=c.pk)
    return render(request, 'projects/contact_form.html', {'form': form, 'contact': None})


@login_required
def contact_edit(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    accessible = _accessible_projects_qs(request.user)
    form = ContactForm(
        request.POST or None,
        instance=contact,
        accessible_projects_queryset=accessible,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Contact updated.')
        return redirect('projects:contact_detail', pk=contact.pk)
    return render(
        request,
        'projects/contact_form.html',
        {'form': form, 'contact': contact},
    )


@login_required
def contact_detail(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    projects = contact.projects.all()
    documents = Document.objects.filter(contact=contact).select_related('uploaded_by')
    return render(
        request,
        'projects/contact_detail.html',
        {
            'contact': contact,
            'linked_projects': projects,
            'documents': documents,
        },
    )


@login_required
def calendar_view(request):
    return render(request, 'projects/calendar.html')


@login_required
def event_create(request):
    accessible = _accessible_projects_qs(request.user)
    form = EventForm(
        request.POST or None,
        user=request.user,
        accessible_projects_queryset=accessible,
    )
    if request.method == 'POST' and form.is_valid():
        ev = form.save(commit=False)
        ev.created_by = request.user
        ev.save()
        form.save_m2m()
        messages.success(request, 'Event created.')
        return redirect('projects:calendar')
    return render(request, 'projects/event_form.html', {'form': form, 'event': None})


@login_required
def event_edit(request, pk):
    accessible = _accessible_projects_qs(request.user)
    event = get_object_or_404(_accessible_events_qs(request.user), pk=pk)
    form = EventForm(
        request.POST or None,
        instance=event,
        user=request.user,
        accessible_projects_queryset=accessible,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Event updated.')
        return redirect('projects:calendar')
    return render(request, 'projects/event_form.html', {'form': form, 'event': event})


@login_required
def event_json(request):
    events = _accessible_events_qs(request.user)
    out = []
    for ev in events:
        end = ev.end_datetime
        if ev.all_day and end is None:
            end = ev.start_datetime
        item = {
            'id': str(ev.pk),
            'title': ev.title,
            'start': ev.start_datetime.isoformat(),
            'end': end.isoformat() if end else None,
            'allDay': ev.all_day,
            'url': reverse('projects:event_edit', args=[ev.pk]),
            'color': _event_type_color(ev.event_type),
        }
        out.append(item)
    return JsonResponse(out, safe=False)


@login_required
def notification_list(request):
    notifications = (
        Notification.objects.filter(recipient=request.user)
        .select_related('actor', 'target_task', 'target_project')
        .order_by('is_read', '-created_at')
    )
    return render(
        request,
        'projects/notification_list.html',
        {'notifications': notifications},
    )


@login_required
@require_POST
def notification_mark_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked read.')
    next_url = request.POST.get('next') or reverse('projects:notification_list')
    return redirect(next_url)


_TASK_STATUS_ORDER = [
    TaskStatus.BACKLOG,
    TaskStatus.TODO,
    TaskStatus.IN_PROGRESS,
    TaskStatus.IN_REVIEW,
    TaskStatus.BLOCKED,
    TaskStatus.DONE,
]
_TASK_STATUS_LABELS = [dict(TaskStatus.choices)[s] for s in _TASK_STATUS_ORDER]

_PRIORITY_ORDER = [
    Priority.LOW,
    Priority.MEDIUM,
    Priority.HIGH,
    Priority.CRITICAL,
]
_PRIORITY_LABELS = [dict(Priority.choices)[p] for p in _PRIORITY_ORDER]


def _active_project_filter():
    return ~Q(status__in=[ProjectStatus.COMPLETED, ProjectStatus.ARCHIVED])


def _accessible_tasks_qs(user):
    return Task.objects.filter(project__in=_accessible_projects_qs(user)).distinct()


def _owner_project_ids(user, project_ids):
    """Project IDs where user is account owner or membership role Owner."""
    base = Project.objects.filter(pk__in=project_ids)
    ids = set(base.filter(owner=user).values_list('id', flat=True))
    ids |= set(
        ProjectMembership.objects.filter(
            user=user,
            role=MembershipRole.OWNER,
            project_id__in=project_ids,
        ).values_list('project_id', flat=True)
    )
    return ids


def _admin_project_ids(user, project_ids):
    return set(
        ProjectMembership.objects.filter(
            user=user,
            role=MembershipRole.ADMIN,
            project_id__in=project_ids,
        ).values_list('project_id', flat=True)
    )


def _team_users(user):
    """Users who share at least one accessible project (owner or member)."""
    projects = _accessible_projects_qs(user)
    if not projects.exists():
        return User.objects.none()
    pids = list(projects.values_list('pk', flat=True))
    owner_ids = set(projects.values_list('owner_id', flat=True))
    member_ids = set(
        ProjectMembership.objects.filter(project_id__in=pids).values_list('user_id', flat=True)
    )
    all_ids = owner_ids | member_ids
    return User.objects.filter(pk__in=all_ids).order_by('username').distinct()


def _user_display(u):
    if not u:
        return 'Unknown'
    full = (u.get_full_name() or '').strip()
    return full or u.get_username()


def _build_dashboard_payload(user):
    """Shared metrics for HTML dashboard and JSON charts."""
    projects_qs = _accessible_projects_qs(user)
    tasks_qs = _accessible_tasks_qs(user)
    today = timezone.localdate()
    now = timezone.now()
    week_end = today + timedelta(days=7)
    horizon = today + timedelta(days=14)

    total_projects = projects_qs.count()
    active_projects_qs = projects_qs.filter(_active_project_filter())
    active_projects_count = active_projects_qs.count()

    total_tasks = tasks_qs.count()
    completed_tasks = tasks_qs.filter(status=TaskStatus.DONE).count()
    overdue_tasks = tasks_qs.filter(
        ~Q(status=TaskStatus.DONE),
        due_date__isnull=False,
        due_date__lt=today,
    ).count()
    tasks_due_this_week = tasks_qs.filter(
        ~Q(status=TaskStatus.DONE),
        due_date__isnull=False,
        due_date__gte=today,
        due_date__lte=week_end,
    ).count()
    open_tasks_assigned_to_me = (
        tasks_qs.filter(assignees=user).exclude(status=TaskStatus.DONE).distinct().count()
    )

    status_counts_raw = dict(
        tasks_qs.values('status').annotate(c=Count('id', distinct=True)).values_list('status', 'c')
    )
    task_status_counts = {dict(TaskStatus.choices)[k]: status_counts_raw.get(k, 0) for k, _ in TaskStatus.choices}

    team = list(_team_users(user))
    project_ids = list(projects_qs.values_list('pk', flat=True))
    workload_by_user = []
    for u in team:
        assigned = tasks_qs.filter(assignees=u)
        open_c = assigned.exclude(status=TaskStatus.DONE).count()
        done_c = assigned.filter(status=TaskStatus.DONE).count()
        overdue_c = assigned.filter(
            ~Q(status=TaskStatus.DONE),
            due_date__isnull=False,
            due_date__lt=today,
        ).count()
        roles = set(
            ProjectMembership.objects.filter(user=u, project_id__in=project_ids).values_list(
                'role', flat=True
            )
        )
        if projects_qs.filter(owner=u).exists():
            roles.add(MembershipRole.OWNER)
        role_labels = sorted({dict(MembershipRole.choices).get(r, r) for r in roles})
        workload_by_user.append(
            {
                'user': u,
                'user_display_name': _user_display(u),
                'role': ', '.join(role_labels) if role_labels else '—',
                'open_tasks': open_c,
                'completed_tasks': done_c,
                'overdue_tasks': overdue_c,
            }
        )

    project_progress = []
    for p in active_projects_qs.order_by('name'):
        p_tasks = tasks_qs.filter(project=p)
        tot = p_tasks.count()
        done = p_tasks.filter(status=TaskStatus.DONE).count()
        pct = round(100.0 * done / tot, 1) if tot else 0.0
        overdue_c = p_tasks.filter(
            ~Q(status=TaskStatus.DONE),
            due_date__isnull=False,
            due_date__lt=today,
        ).count()
        open_c = p_tasks.exclude(status=TaskStatus.DONE).count()
        days_until = None
        if p.due_date:
            days_until = (p.due_date - today).days
        project_progress.append(
            {
                'name': p.name,
                'status': p.get_status_display(),
                'priority': p.get_priority_display(),
                'total_tasks': tot,
                'done_tasks': done,
                'percent_complete': pct,
                'overdue_count': overdue_c,
                'due_date': p.due_date,
                'days_until_due': days_until,
                'open_tasks': open_c,
            }
        )

    upcoming_deadlines = (
        tasks_qs.filter(
            ~Q(status=TaskStatus.DONE),
            due_date__isnull=False,
            due_date__gte=today,
            due_date__lte=horizon,
        )
        .select_related('project')
        .prefetch_related('assignees')
        .order_by('due_date')[:10]
    )

    comment_qs = (
        Comment.objects.filter(task__project__in=projects_qs)
        .select_related('author', 'task', 'task__project')
        .order_by('-created_at')[:20]
    )
    task_touch_qs = tasks_qs.select_related('project', 'created_by').order_by('-updated_at')[:20]
    activity = []
    for c in comment_qs:
        activity.append(
            {
                'timestamp': c.created_at,
                'actor_name': _user_display(c.author),
                'description': 'commented on',
                'task_name': c.task.title,
                'project_name': c.task.project.name,
            }
        )
    for t in task_touch_qs:
        activity.append(
            {
                'timestamp': t.updated_at,
                'actor_name': _user_display(t.created_by) if t.created_by else 'System',
                'description': 'task record updated',
                'task_name': t.title,
                'project_name': t.project.name,
            }
        )
    activity.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activity = activity[:15]

    unread_notifications = Notification.objects.filter(recipient=user, is_read=False).count()

    local_now = timezone.localtime(now)
    week_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(
        days=local_now.weekday()
    )
    weekly_values = []
    for i in range(7):
        day_start = timezone.make_aware(
            datetime.combine((week_start + timedelta(days=i)).date(), datetime.min.time()),
            timezone.get_current_timezone(),
        )
        day_end = day_start + timedelta(days=1)
        weekly_values.append(
            tasks_qs.filter(
                status=TaskStatus.DONE,
                updated_at__gte=day_start,
                updated_at__lt=day_end,
            ).count()
        )

    workload_chart = {'labels': [], 'cto_open': [], 'cspo_open': []}
    for u in team:
        workload_chart['labels'].append(_user_display(u))
        oids = _owner_project_ids(u, project_ids)
        aids = _admin_project_ids(u, project_ids)
        cto_open = (
            tasks_qs.filter(project_id__in=oids, assignees=u)
            .exclude(status=TaskStatus.DONE)
            .distinct()
            .count()
        )
        cspo_open = (
            tasks_qs.filter(project_id__in=aids, assignees=u)
            .exclude(status=TaskStatus.DONE)
            .distinct()
            .count()
        )
        workload_chart['cto_open'].append(cto_open)
        workload_chart['cspo_open'].append(cspo_open)

    project_completion_labels = []
    project_completion_values = []
    for row in sorted(project_progress, key=lambda r: r['percent_complete'], reverse=True):
        project_completion_labels.append(row['name'])
        project_completion_values.append(float(row['percent_complete']))

    priority_values = [
        tasks_qs.filter(priority=p).count() for p in _PRIORITY_ORDER
    ]
    task_status_values = [status_counts_raw.get(s, 0) for s in _TASK_STATUS_ORDER]

    weekday_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    return {
        'total_projects': total_projects,
        'active_projects': active_projects_count,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'tasks_due_this_week': tasks_due_this_week,
        'open_tasks_assigned_to_me': open_tasks_assigned_to_me,
        'project_progress': project_progress,
        'task_status_counts': task_status_counts,
        'workload_by_user': workload_by_user,
        'upcoming_deadlines': upcoming_deadlines,
        'recent_activity': recent_activity,
        'unread_notifications': unread_notifications,
        'urgent_deadline_cutoff': today + timedelta(days=3),
        '_json': {
            'task_status': {'labels': _TASK_STATUS_LABELS, 'values': task_status_values},
            'workload': workload_chart,
            'project_completion': {
                'labels': project_completion_labels,
                'values': project_completion_values,
            },
            'tasks_by_priority': {'labels': _PRIORITY_LABELS, 'values': priority_values},
            'weekly_completions': {'labels': weekday_labels, 'values': weekly_values},
        },
    }


@login_required
def dashboard(request):
    projects_qs = _accessible_projects_qs(request.user)
    if not projects_qs.exists():
        return render(
            request,
            'projects/dashboard.html',
            {'empty_state': True},
        )

    payload = _build_dashboard_payload(request.user)
    ctx = {k: v for k, v in payload.items() if k != '_json'}
    return render(request, 'projects/dashboard.html', {'empty_state': False, **ctx})


@login_required
def dashboard_data(request):
    projects_qs = _accessible_projects_qs(request.user)
    if not projects_qs.exists():
        data = {
            'task_status': {'labels': _TASK_STATUS_LABELS, 'values': [0, 0, 0, 0, 0, 0]},
            'workload': {'labels': [], 'cto_open': [], 'cspo_open': []},
            'project_completion': {'labels': [], 'values': []},
            'tasks_by_priority': {'labels': _PRIORITY_LABELS, 'values': [0, 0, 0, 0]},
            'weekly_completions': {
                'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                'values': [0, 0, 0, 0, 0, 0, 0],
            },
            'summary': {
                'total_projects': 0,
                'active_projects': 0,
                'total_tasks': 0,
                'completed_tasks': 0,
                'overdue_tasks': 0,
                'tasks_due_this_week': 0,
                'open_tasks_assigned_to_me': 0,
            },
        }
        return JsonResponse(data)

    payload = _build_dashboard_payload(request.user)
    data = dict(payload['_json'])
    data['summary'] = {
        'total_projects': payload['total_projects'],
        'active_projects': payload['active_projects'],
        'total_tasks': payload['total_tasks'],
        'completed_tasks': payload['completed_tasks'],
        'overdue_tasks': payload['overdue_tasks'],
        'tasks_due_this_week': payload['tasks_due_this_week'],
        'open_tasks_assigned_to_me': payload['open_tasks_assigned_to_me'],
    }
    return JsonResponse(data)

