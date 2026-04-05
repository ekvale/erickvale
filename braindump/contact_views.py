"""Owner-only personal / work contacts (address book)."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .authz import braindump_configured, is_braindump_owner
from .forms import PersonalContactAttachmentForm, PersonalContactForm
from .models import PersonalContact, PersonalContactAttachment

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
    return render(
        request,
        'braindump/contacts/detail.html',
        {'contact': contact, 'attach_form': attach_form},
    )


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
