from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from projects.models import Task
from projects.views import _accessible_projects_qs

from .forms import ContactForm, ContactImportFileForm
from .gmail_import import gmail_oauth_configured, import_gmail_contacts
from .import_parsers import parse_uploaded_file
from .import_service import import_parsed_rows
from .models import Contact, ContactSource


def _accessible_tasks_qs(user):
    return Task.objects.filter(
        project__in=_accessible_projects_qs(user)
    ).distinct()


class ContactListView(LoginRequiredMixin, ListView):
    model = Contact
    template_name = 'contacts/contact_list.html'
    context_object_name = 'contacts'
    paginate_by = 50

    def get_queryset(self):
        qs = Contact.objects.prefetch_related('projects', 'tasks')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(display_name__icontains=q)
                | Q(email__icontains=q)
                | Q(company__icontains=q)
            )
        source = self.request.GET.get('source', '').strip()
        if source:
            qs = qs.filter(source=source)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['q'] = self.request.GET.get('q', '')
        ctx['source'] = self.request.GET.get('source', '')
        ctx['source_choices'] = ContactSource.choices
        ctx['gmail_configured'] = gmail_oauth_configured()
        return ctx


class ContactDetailView(LoginRequiredMixin, DetailView):
    model = Contact
    template_name = 'contacts/contact_detail.html'
    context_object_name = 'contact'

    def get_queryset(self):
        return Contact.objects.prefetch_related('projects', 'tasks')


class ContactCreateView(LoginRequiredMixin, CreateView):
    model = Contact
    form_class = ContactForm
    template_name = 'contacts/contact_form.html'
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['projects_queryset'] = _accessible_projects_qs(self.request.user)
        kwargs['tasks_queryset'] = _accessible_tasks_qs(self.request.user)
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Contact created.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('contacts:detail', kwargs={'pk': self.object.pk})


class ContactUpdateView(LoginRequiredMixin, UpdateView):
    model = Contact
    form_class = ContactForm
    template_name = 'contacts/contact_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['projects_queryset'] = _accessible_projects_qs(self.request.user)
        kwargs['tasks_queryset'] = _accessible_tasks_qs(self.request.user)
        return kwargs

    def get_success_url(self):
        return reverse_lazy('contacts:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Contact updated.')
        return super().form_valid(form)


class ContactDeleteView(LoginRequiredMixin, DeleteView):
    model = Contact
    template_name = 'contacts/contact_confirm_delete.html'
    success_url = reverse_lazy('contacts:list')

    def form_valid(self, form):
        messages.success(self.request, 'Contact deleted.')
        return super().form_valid(form)


@login_required
def contact_import_page(request):
    return render(
        request,
        'contacts/import.html',
        {
            'file_form': ContactImportFileForm(),
            'gmail_configured': gmail_oauth_configured(),
        },
    )


@login_required
def import_gmail_contacts_view(request):
    result = import_gmail_contacts(max_messages=500)
    if result.error:
        messages.error(request, result.error)
    else:
        messages.success(
            request,
            f'{result.added} contacts added, {result.skipped_existing} already existed.',
        )
    return redirect('contacts:list')


@login_required
@require_POST
def import_file_contacts(request):
    form = ContactImportFileForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, 'Choose a valid file to upload.')
        return redirect('contacts:import')
    upload = form.cleaned_data['file']
    try:
        rows = parse_uploaded_file(upload.name, upload.read())
    except (ValueError, Exception) as exc:
        messages.error(request, f'Could not parse file: {exc}')
        return redirect('contacts:import')
    result = import_parsed_rows(rows)
    messages.success(
        request,
        f'{result.added} contacts added, {result.skipped_existing} already existed.',
    )
    return redirect('contacts:list')
