from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import SiteContactForm


def _safe_next_path(request):
    """Return a relative next URL safe for redirect after login."""
    nxt = (request.POST.get("next") or request.GET.get("next") or "").strip()
    if not nxt:
        return reverse("homepage")
    if nxt.startswith("/") and url_has_allowed_host_and_scheme(
        url=nxt,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return nxt
    return reverse("homepage")


def coming_soon(request):
    """Public placeholder while the marketing site is under construction."""
    if request.user.is_authenticated:
        return redirect("homepage")
    next_target = "/"
    raw = (request.GET.get("next") or "").strip()
    if raw.startswith("/") and url_has_allowed_host_and_scheme(
        url=raw,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_target = raw
    login_url = reverse("login") + "?" + urlencode({"next": next_target})
    return render(
        request,
        "erickvale/coming_soon.html",
        {
            "login_url": login_url,
            "contact_email": settings.CONTACT_EMAIL,
        },
    )


def homepage(request):
    """Public landing page (HTAC-focused)."""
    return render(request, 'erickvale/homepage.html')


def about(request):
    """About page view."""
    return render(request, 'erickvale/about.html')


def services(request):
    """Professional services page."""
    return render(request, 'erickvale/services.html')


def contact(request):
    """Public contact form; sends notification email on valid POST."""
    if request.method == 'POST':
        form = SiteContactForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            subject = f"New Contact Form Submission — {data['inquiry_type']}"
            org = data.get('organization') or '(not provided)'
            body = (
                f"Name: {data['name']}\n"
                f"Organization: {org}\n"
                f"Email: {data['email']}\n"
                f"Inquiry type: {data['inquiry_type']}\n\n"
                f"Message:\n{data['message']}\n"
            )
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            messages.success(
                request,
                "Your message has been sent. I'll be in touch shortly.",
            )
            return redirect('contact')
    else:
        form = SiteContactForm()

    return render(
        request,
        'erickvale/contact.html',
        {
            'form': form,
            'contact_email': settings.CONTACT_EMAIL,
        },
    )


def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        return redirect('homepage')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect(_safe_next_path(request))
    else:
        form = AuthenticationForm()

    return render(
        request,
        'erickvale/login.html',
        {
            'form': form,
            'next': request.GET.get('next', ''),
        },
    )


def logout_view(request):
    """User logout view."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('homepage')
