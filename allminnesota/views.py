"""
Views for All Minnesota operations dashboard.
All views require login.
"""
import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from decimal import Decimal

from .models import (
    Contact,
    DistributionSite,
    BusinessPlan,
    PlanSection,
    KPI,
    KPIUpdateHistory,
    Task,
    SocialMediaPost,
    TaskStatus,
)
from .forms import (
    ContactForm,
    ContactFilterForm,
    DistributionSiteForm,
    BusinessPlanForm,
    PlanSectionForm,
    KPIForm,
    KPIUpdateValueForm,
    KPIFilterForm,
    TaskForm,
    TaskFilterForm,
    SocialMediaPostForm,
    SocialMediaFilterForm,
)


# --- Dashboard ---

@login_required
def dashboard(request):
    """Main dashboard: summary cards, KPI progress, recent activity, quick links."""
    today = timezone.now().date()
    # Summary counts
    total_contacts = Contact.objects.filter(is_active=True).count()
    active_sites = DistributionSite.objects.filter(is_active=True).count()
    open_tasks = Task.objects.exclude(status=TaskStatus.COMPLETED).count()
    # Upcoming events: tasks with category EVENT and due_date >= today
    upcoming_events = Task.objects.filter(
        category='EVENT',
        due_date__gte=today,
        status__in=[TaskStatus.TODO, TaskStatus.IN_PROGRESS],
    ).order_by('due_date')[:5]
    # KPIs for progress bars (top 5 by category or all if fewer)
    kpis = KPI.objects.all().order_by('category', 'kpi_name')[:8]
    # Recent activity: tasks updated, new contacts, posts scheduled
    recent_tasks = Task.objects.select_related('assigned_to', 'created_by').order_by('-updated_date')[:5]
    recent_contacts = Contact.objects.select_related('created_by').order_by('-date_added')[:5]
    recent_posts = SocialMediaPost.objects.filter(
        status__in=['SCHEDULED', 'PUBLISHED']
    ).order_by('-scheduled_date', '-created_date')[:5]
    context = {
        'total_contacts': total_contacts,
        'active_sites': active_sites,
        'open_tasks': open_tasks,
        'upcoming_events': upcoming_events,
        'kpis': kpis,
        'recent_tasks': recent_tasks,
        'recent_contacts': recent_contacts,
        'recent_posts': recent_posts,
    }
    return render(request, 'allminnesota/dashboard.html', context)


# --- Contacts ---

@login_required
def contact_list(request):
    """List contacts with search and filter by contact_type."""
    qs = Contact.objects.select_related('created_by').order_by('last_name', 'first_name')
    form = ContactFilterForm(request.GET or None)
    if form.is_valid():
        if form.cleaned_data.get('search'):
            s = form.cleaned_data['search']
            qs = qs.filter(
                Q(first_name__icontains=s) | Q(last_name__icontains=s) |
                Q(email__icontains=s) | Q(notes__icontains=s)
            )
        if form.cleaned_data.get('contact_type'):
            qs = qs.filter(contact_type=form.cleaned_data['contact_type'])
    paginator = Paginator(qs, 20)
    page = request.GET.get('page', 1)
    contacts = paginator.get_page(page)
    return render(request, 'allminnesota/contact_list.html', {
        'contacts': contacts,
        'form': form,
    })


@login_required
def contact_detail(request, pk):
    """Detail view for a single contact."""
    contact = get_object_or_404(Contact, pk=pk)
    sites = contact.distribution_sites.all()
    return render(request, 'allminnesota/contact_detail.html', {
        'contact': contact,
        'sites': sites,
    })


@login_required
def contact_create(request):
    """Create a new contact."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact = form.save(commit=False)
            contact.created_by = request.user
            contact.save()
            messages.success(request, f'Contact "{contact}" created.')
            return redirect('allminnesota:contact_detail', pk=contact.pk)
    else:
        form = ContactForm()
    return render(request, 'allminnesota/contact_form.html', {'form': form, 'contact': None})


@login_required
def contact_edit(request, pk):
    """Edit an existing contact."""
    contact = get_object_or_404(Contact, pk=pk)
    if request.method == 'POST':
        form = ContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request, f'Contact "{contact}" updated.')
            return redirect('allminnesota:contact_detail', pk=contact.pk)
    else:
        form = ContactForm(instance=contact)
    return render(request, 'allminnesota/contact_form.html', {'form': form, 'contact': contact})


@login_required
def contact_export_csv(request):
    """Export contacts to CSV."""
    qs = Contact.objects.all().order_by('last_name', 'first_name')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="allminnesota_contacts.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'First Name', 'Last Name', 'Email', 'Phone', 'Type', 'Address', 'City', 'State', 'ZIP', 'Notes', 'Active', 'Date Added'
    ])
    for c in qs:
        writer.writerow([
            c.first_name, c.last_name, c.email, c.phone, c.get_contact_type_display(),
            c.address, c.city, c.state, c.zip_code, c.notes, c.is_active, c.date_added,
        ])
    return response


# --- Distribution Sites ---

@login_required
def site_list(request):
    """List distribution sites with filter by region."""
    qs = DistributionSite.objects.select_related('contact_person').order_by('region', 'site_name')
    region = request.GET.get('region')
    if region in ('TWIN_CITIES', 'GREATER_MINNESOTA'):
        qs = qs.filter(region=region)
    paginator = Paginator(qs, 20)
    page = request.GET.get('page', 1)
    sites = paginator.get_page(page)
    return render(request, 'allminnesota/site_list.html', {'sites': sites, 'current_region': region})


@login_required
def site_detail(request, pk):
    """Detail view for a distribution site (contacts and tasks)."""
    site = get_object_or_404(DistributionSite.objects.select_related('contact_person'), pk=pk)
    tasks = site.tasks.all().select_related('assigned_to').order_by('-due_date')[:20]
    return render(request, 'allminnesota/site_detail.html', {'site': site, 'tasks': tasks})


@login_required
def site_create(request):
    """Create a new distribution site."""
    if request.method == 'POST':
        form = DistributionSiteForm(request.POST)
        if form.is_valid():
            site = form.save()
            messages.success(request, f'Site "{site.site_name}" created.')
            return redirect('allminnesota:site_detail', pk=site.pk)
    else:
        form = DistributionSiteForm()
    return render(request, 'allminnesota/site_form.html', {'form': form, 'site': None})


@login_required
def site_edit(request, pk):
    """Edit a distribution site."""
    site = get_object_or_404(DistributionSite, pk=pk)
    if request.method == 'POST':
        form = DistributionSiteForm(request.POST, instance=site)
        if form.is_valid():
            form.save()
            messages.success(request, f'Site "{site.site_name}" updated.')
            return redirect('allminnesota:site_detail', pk=site.pk)
    else:
        form = DistributionSiteForm(instance=site)
    return render(request, 'allminnesota/site_form.html', {'form': form, 'site': site})


# --- Business Plans ---

@login_required
def plan_list(request):
    """List business plans."""
    plans = BusinessPlan.objects.select_related('owner').order_by('-updated_date')
    return render(request, 'allminnesota/plan_list.html', {'plans': plans})


@login_required
def plan_detail(request, pk):
    """Detail view with sections in order."""
    plan = get_object_or_404(BusinessPlan.objects.prefetch_related('sections'), pk=pk)
    sections = list(plan.sections.all().order_by('order'))
    return render(request, 'allminnesota/plan_detail.html', {'plan': plan, 'sections': sections})


@login_required
def plan_create(request):
    """Create a new business plan."""
    if request.method == 'POST':
        form = BusinessPlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.owner = request.user
            plan.save()
            messages.success(request, f'Plan "{plan.title}" created.')
            return redirect('allminnesota:plan_detail', pk=plan.pk)
    else:
        form = BusinessPlanForm()
    return render(request, 'allminnesota/plan_form.html', {'form': form, 'plan': None})


@login_required
def plan_edit(request, pk):
    """Edit a business plan."""
    plan = get_object_or_404(BusinessPlan, pk=pk)
    if request.method == 'POST':
        form = BusinessPlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, f'Plan "{plan.title}" updated.')
            return redirect('allminnesota:plan_detail', pk=plan.pk)
    else:
        form = BusinessPlanForm(instance=plan)
    return render(request, 'allminnesota/plan_form.html', {'form': form, 'plan': plan})


@login_required
def section_create(request, plan_pk):
    """Add a section to a plan."""
    plan = get_object_or_404(BusinessPlan, pk=plan_pk)
    if request.method == 'POST':
        form = PlanSectionForm(request.POST)
        if form.is_valid():
            section = form.save(commit=False)
            section.plan = plan
            if not section.order:
                section.order = (plan.sections.aggregate(Count('id'))['id__count'] or 0)
            section.save()
            messages.success(request, f'Section "{section.title}" added.')
            return redirect('allminnesota:plan_detail', pk=plan.pk)
    else:
        next_order = (plan.sections.aggregate(Count('id'))['id__count'] or 0)
        form = PlanSectionForm(initial={'order': next_order})
    return render(request, 'allminnesota/section_form.html', {'form': form, 'plan': plan, 'section': None})


@login_required
def section_edit(request, plan_pk, pk):
    """Edit a plan section."""
    plan = get_object_or_404(BusinessPlan, pk=plan_pk)
    section = get_object_or_404(PlanSection, plan=plan, pk=pk)
    if request.method == 'POST':
        form = PlanSectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, f'Section "{section.title}" updated.')
            return redirect('allminnesota:plan_detail', pk=plan.pk)
    else:
        form = PlanSectionForm(instance=section)
    return render(request, 'allminnesota/section_form.html', {'form': form, 'plan': plan, 'section': section})


@login_required
@require_http_methods(['POST'])
def section_reorder(request, plan_pk):
    """Reorder sections (POST: section_ids comma-separated). Two-phase update to respect unique_together."""
    plan = get_object_or_404(BusinessPlan, pk=plan_pk)
    section_ids = request.POST.get('section_ids', '')
    if section_ids:
        ids = [int(x) for x in section_ids.split(',') if x.strip().isdigit()]
        # Phase 1: set all to high temp order to avoid unique_together violation
        for sid in ids:
            PlanSection.objects.filter(plan=plan, pk=sid).update(order=10000 + sid)
        # Phase 2: set final order
        for order, sid in enumerate(ids):
            PlanSection.objects.filter(plan=plan, pk=sid).update(order=order)
    messages.success(request, 'Sections reordered.')
    return redirect('allminnesota:plan_detail', pk=plan.pk)


# --- KPIs ---

@login_required
def kpi_list(request):
    """Dashboard-style KPI list with progress bars and filter by category."""
    qs = KPI.objects.select_related('updated_by').order_by('category', 'kpi_name')
    form = KPIFilterForm(request.GET or None)
    if form.is_valid() and form.cleaned_data.get('category'):
        qs = qs.filter(category=form.cleaned_data['category'])
    return render(request, 'allminnesota/kpi_list.html', {'kpis': qs, 'form': form})


@login_required
def kpi_detail(request, pk):
    """KPI detail with update form and history log."""
    kpi = get_object_or_404(KPI, pk=pk)
    history = kpi.update_history.select_related('updated_by').order_by('-updated_at')[:20]
    return render(request, 'allminnesota/kpi_detail.html', {'kpi': kpi, 'history': history})


@login_required
def kpi_update_value(request, pk):
    """Update current value and record in history."""
    kpi = get_object_or_404(KPI, pk=pk)
    if request.method == 'POST':
        form = KPIUpdateValueForm(request.POST)
        if form.is_valid():
            prev = kpi.current_value
            kpi.current_value = form.cleaned_data['new_value']
            kpi.updated_by = request.user
            kpi.save()
            KPIUpdateHistory.objects.create(
                kpi=kpi,
                previous_value=prev,
                new_value=kpi.current_value,
                notes=form.cleaned_data.get('notes', ''),
                updated_by=request.user,
            )
            messages.success(request, f'KPI "{kpi.kpi_name}" updated to {kpi.current_value}.')
            return redirect('allminnesota:kpi_detail', pk=kpi.pk)
    else:
        form = KPIUpdateValueForm(initial={'new_value': kpi.current_value})
    return render(request, 'allminnesota/kpi_update_value.html', {'form': form, 'kpi': kpi})


# --- Tasks ---

@login_required
def task_list(request):
    """List tasks with filters (assignee, priority, status, category)."""
    qs = Task.objects.select_related('assigned_to', 'created_by', 'related_site').order_by('-due_date', 'priority')
    form = TaskFilterForm(request.GET or None)
    if form.is_valid():
        if form.cleaned_data.get('search'):
            s = form.cleaned_data['search']
            qs = qs.filter(Q(title__icontains=s) | Q(description__icontains=s))
        if form.cleaned_data.get('assigned_to'):
            qs = qs.filter(assigned_to=form.cleaned_data['assigned_to'])
        if form.cleaned_data.get('priority'):
            qs = qs.filter(priority=form.cleaned_data['priority'])
        if form.cleaned_data.get('status'):
            qs = qs.filter(status=form.cleaned_data['status'])
        if form.cleaned_data.get('category'):
            qs = qs.filter(category=form.cleaned_data['category'])
    paginator = Paginator(qs, 25)
    page = request.GET.get('page', 1)
    tasks = paginator.get_page(page)
    return render(request, 'allminnesota/task_list.html', {'tasks': tasks, 'form': form})


@login_required
def task_board(request):
    """Kanban-style board: TODO, IN_PROGRESS, COMPLETED, ON_HOLD."""
    columns = [
        (TaskStatus.TODO, 'To Do'),
        (TaskStatus.IN_PROGRESS, 'In Progress'),
        (TaskStatus.COMPLETED, 'Completed'),
        (TaskStatus.ON_HOLD, 'On Hold'),
    ]
    board = []
    for status_value, label in columns:
        tasks = Task.objects.filter(status=status_value).select_related(
            'assigned_to', 'related_site'
        ).order_by('priority', '-due_date')
        board.append({'status': status_value, 'label': label, 'tasks': list(tasks)})
    return render(request, 'allminnesota/task_board.html', {'board': board})


@login_required
def task_detail(request, pk):
    """Detail view for a task."""
    task = get_object_or_404(
        Task.objects.select_related('assigned_to', 'created_by', 'related_site'),
        pk=pk,
    )
    return render(request, 'allminnesota/task_detail.html', {'task': task})


@login_required
def task_create(request):
    """Create a new task."""
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            messages.success(request, f'Task "{task.title}" created.')
            return redirect('allminnesota:task_detail', pk=task.pk)
    else:
        form = TaskForm()
    return render(request, 'allminnesota/task_form.html', {'form': form, 'task': None})


@login_required
def task_edit(request, pk):
    """Edit a task."""
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, f'Task "{task.title}" updated.')
            return redirect('allminnesota:task_detail', pk=task.pk)
    else:
        form = TaskForm(instance=task)
    return render(request, 'allminnesota/task_form.html', {'form': form, 'task': task})


@login_required
@require_http_methods(['GET', 'POST'])
def task_delete(request, pk):
    """Delete a task (confirm via POST)."""
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        title = task.title
        task.delete()
        messages.success(request, f'Task "{title}" deleted.')
        return redirect('allminnesota:task_list')
    return render(request, 'allminnesota/task_confirm_delete.html', {'task': task})


# --- Social Media ---

@login_required
def social_list(request):
    """List social media posts with status indicators and filter."""
    qs = SocialMediaPost.objects.select_related('created_by').order_by('-scheduled_date', '-created_date')
    form = SocialMediaFilterForm(request.GET or None)
    if form.is_valid():
        if form.cleaned_data.get('platform'):
            qs = qs.filter(platform=form.cleaned_data['platform'])
        if form.cleaned_data.get('status'):
            qs = qs.filter(status=form.cleaned_data['status'])
    paginator = Paginator(qs, 20)
    page = request.GET.get('page', 1)
    posts = paginator.get_page(page)
    return render(request, 'allminnesota/social_list.html', {'posts': posts, 'form': form})


@login_required
def social_calendar(request):
    """Calendar view of scheduled posts."""
    # Simple list of scheduled posts by date for calendar display
    posts = SocialMediaPost.objects.filter(
        status__in=['SCHEDULED', 'PUBLISHED'],
        scheduled_date__isnull=False,
    ).order_by('scheduled_date')
    return render(request, 'allminnesota/social_calendar.html', {'posts': posts})


@login_required
def social_detail(request, pk):
    """Detail view for a social media post."""
    post = get_object_or_404(SocialMediaPost, pk=pk)
    return render(request, 'allminnesota/social_detail.html', {'post': post})


@login_required
def social_create(request):
    """Create a new social media post."""
    if request.method == 'POST':
        form = SocialMediaPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.created_by = request.user
            post.save()
            messages.success(request, f'Post "{post.title}" created.')
            return redirect('allminnesota:social_detail', pk=post.pk)
    else:
        form = SocialMediaPostForm()
    return render(request, 'allminnesota/social_form.html', {'form': form, 'post': None})


@login_required
def social_edit(request, pk):
    """Edit a social media post."""
    post = get_object_or_404(SocialMediaPost, pk=pk)
    if request.method == 'POST':
        form = SocialMediaPostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, f'Post "{post.title}" updated.')
            return redirect('allminnesota:social_detail', pk=post.pk)
    else:
        form = SocialMediaPostForm(instance=post)
    return render(request, 'allminnesota/social_form.html', {'form': form, 'post': post})
