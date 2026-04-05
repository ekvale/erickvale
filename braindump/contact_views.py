"""Owner-only personal / work contacts (address book)."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from dream_blue.emailing import DreamBlueEmailConfigError

from .authz import braindump_configured, is_braindump_owner
from .forms import (
    ContactEmailMessageForm,
    ContactEmailScheduleForm,
    PersonalContactAttachmentForm,
    PersonalContactForm,
)
from .models import ContactScheduledEmail, PersonalContact, PersonalContactAttachment

_MAX_ATTACHMENT_BYTES = 15 * 1024 * 1024


def _require_owner(request):
    if not braindump_configured():
        raise PermissionDenied('Brain dump is not configured (set BRAINDUMP_OWNER_USERNAME or ID).')
    if not is_braindump_owner(request.user):
        raise PermissionDenied()


def _contact_qs(request):
    return PersonalContact.objects.filter(user=request.user)


@login_required
@require_http_methods(['GET'])
def contact_list(request):
    _require_owner(request)
    qs = _contact_qs(request)
    kind = (request.GET.get('kind') or '').strip()
    if kind in ('work', 'personal', 'both'):
        qs = qs.filter(relationship_kind=kind)
    q = (request.GET.get('q') or '').strip()
    if q:
        qs = qs.filter(
            Q(display_name__icontains=q)
            | Q(notes__icontains=q)
            | Q(email__icontains=q)
            | Q(company__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
        )
    contacts = list(qs[:500])
    return render(
        request,
        'braindump/contacts/list.html',
        {
            'contacts': contacts,
            'filter_kind': kind,
            'search_q': q,
        },
    )


@login_required
@require_http_methods(['GET', 'POST'])
def contact_create(request):
    _require_owner(request)
    if request.method == 'POST':
        form = PersonalContactForm(request.POST)
        if form.is_valid():
            c = form.save(commit=False)
            c.user = request.user
            c.save()
            messages.success(request, f'Saved {c.display_name}.')
            return HttpResponseRedirect(reverse('braindump:contact_detail', args=[c.pk]))
    else:
        form = PersonalContactForm()
    return render(
        request,
        'braindump/contacts/form.html',
        {'form': form, 'is_new': True, 'contact': None},
    )


@login_required
@require_http_methods(['GET', 'POST'])
def contact_edit(request, pk: int):
    _require_owner(request)
    contact = get_object_or_404(PersonalContact, pk=pk, user=request.user)
    if request.method == 'POST':
        form = PersonalContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contact updated.')
            return HttpResponseRedirect(reverse('braindump:contact_detail', args=[contact.pk]))
    else:
        form = PersonalContactForm(instance=contact)
    return render(
        request,
        'braindump/contacts/form.html',
        {'form': form, 'is_new': False, 'contact': contact},
    )


@login_required
@require_http_methods(['GET'])
def contact_detail(request, pk: int):
    _require_owner(request)
    contact = get_object_or_404(
        PersonalContact.objects.prefetch_related('attachments'),
        pk=pk,
        user=request.user,
    )
    attach_form = PersonalContactAttachmentForm()
    email_form = ContactEmailMessageForm(prefix='send')
    schedule_form = ContactEmailScheduleForm(prefix='sched')
    return render(
        request,
        'braindump/contacts/detail.html',
        {
            'contact': contact,
            'attach_form': attach_form,
            'email_form': email_form,
            'schedule_form': schedule_form,
        },
    )


@login_required
@require_http_methods(['POST'])
def contact_email_send_now(request, pk: int):
    _require_owner(request)
    contact = get_object_or_404(PersonalContact, pk=pk, user=request.user)
    if not (contact.email or '').strip():
        messages.error(request, 'This contact has no email address.')
        return HttpResponseRedirect(reverse('braindump:contact_detail', args=[pk]))
    form = ContactEmailMessageForm(request.POST, prefix='send')
    if not form.is_valid():
        messages.error(request, 'Check subject and message.')
        return HttpResponseRedirect(reverse('braindump:contact_detail', args=[pk]))
    from .contact_outbound import send_contact_email

    try:
        send_contact_email(
            to_email=contact.email.strip(),
            subject=form.cleaned_data['subject'],
            body=form.cleaned_data['body'],
        )
    except DreamBlueEmailConfigError as e:
        messages.error(request, str(e))
    else:
        messages.success(request, f'Email sent to {contact.display_name}.')
    return HttpResponseRedirect(reverse('braindump:contact_detail', args=[pk]))


@login_required
@require_http_methods(['POST'])
def contact_email_schedule(request, pk: int):
    _require_owner(request)
    contact = get_object_or_404(PersonalContact, pk=pk, user=request.user)
    if not (contact.email or '').strip():
        messages.error(request, 'This contact has no email address.')
        return HttpResponseRedirect(reverse('braindump:contact_detail', args=[pk]))
    form = ContactEmailScheduleForm(request.POST, prefix='sched')
    if not form.is_valid():
        messages.error(request, 'Check subject, message, and date/time.')
        return HttpResponseRedirect(reverse('braindump:contact_detail', args=[pk]))
    when = form.cleaned_data['scheduled_for']
    if when <= timezone.now():
        messages.error(request, 'Schedule time must be in the future.')
        return HttpResponseRedirect(reverse('braindump:contact_detail', args=[pk]))
    ContactScheduledEmail.objects.create(
        user=request.user,
        contact=contact,
        subject=form.cleaned_data['subject'],
        body=form.cleaned_data['body'],
        scheduled_for=when,
    )
    messages.success(
        request,
        f'Message scheduled for {contact.display_name} ({when.strftime("%Y-%m-%d %H:%M")}).',
    )
    return HttpResponseRedirect(reverse('braindump:contact_detail', args=[pk]))


@login_required
@require_http_methods(['GET'])
def contact_scheduled_email_list(request):
    _require_owner(request)
    pending = list(
        ContactScheduledEmail.objects.filter(
            user=request.user, status=ContactScheduledEmail.Status.PENDING
        )
        .select_related('contact')
        .order_by('scheduled_for', 'pk')[:200]
    )
    recent = list(
        ContactScheduledEmail.objects.filter(user=request.user)
        .exclude(status=ContactScheduledEmail.Status.PENDING)
        .select_related('contact')
        .order_by('-sent_at', '-created_at')[:50]
    )
    return render(
        request,
        'braindump/contacts/scheduled_emails.html',
        {'pending': pending, 'recent': recent},
    )


@login_required
@require_http_methods(['POST'])
def contact_scheduled_email_cancel(request, sched_pk: int):
    _require_owner(request)
    row = get_object_or_404(
        ContactScheduledEmail,
        pk=sched_pk,
        user=request.user,
        status=ContactScheduledEmail.Status.PENDING,
    )
    row.status = ContactScheduledEmail.Status.CANCELLED
    row.save(update_fields=['status'])
    messages.success(request, 'Scheduled message cancelled.')
    return HttpResponseRedirect(reverse('braindump:contact_scheduled_emails'))


@login_required
@require_http_methods(['POST'])
def contact_delete(request, pk: int):
    _require_owner(request)
    contact = get_object_or_404(PersonalContact, pk=pk, user=request.user)
    name = contact.display_name
    contact.delete()
    messages.success(request, f'Removed {name}.')
    return HttpResponseRedirect(reverse('braindump:contact_list'))


@login_required
@require_http_methods(['POST'])
def contact_attachment_add(request, pk: int):
    _require_owner(request)
    contact = get_object_or_404(PersonalContact, pk=pk, user=request.user)
    form = PersonalContactAttachmentForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, 'Choose a file to upload.')
        return HttpResponseRedirect(reverse('braindump:contact_detail', args=[contact.pk]))
    f = request.FILES.get('file')
    if f and f.size > _MAX_ATTACHMENT_BYTES:
        messages.error(request, 'File too large (max 15 MB).')
        return HttpResponseRedirect(reverse('braindump:contact_detail', args=[contact.pk]))
    att = form.save(commit=False)
    att.contact = contact
    att.save()
    messages.success(request, 'File attached.')
    return HttpResponseRedirect(reverse('braindump:contact_detail', args=[contact.pk]))


@login_required
@require_http_methods(['POST'])
def contact_attachment_delete(request, pk: int, att_pk: int):
    _require_owner(request)
    contact = get_object_or_404(PersonalContact, pk=pk, user=request.user)
    att = get_object_or_404(PersonalContactAttachment, pk=att_pk, contact=contact)
    att.delete()
    messages.success(request, 'Attachment removed.')
    return HttpResponseRedirect(reverse('braindump:contact_detail', args=[contact.pk]))
