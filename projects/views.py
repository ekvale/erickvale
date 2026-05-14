from django.contrib import messages
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
    Project,
    ProjectMembership,
    ProjectStatus,
    Task,
    TaskStatus,
)


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

