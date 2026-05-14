from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.core.mail import send_mail
from django.shortcuts import redirect, render

from .forms import SiteContactForm


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
            next_url = request.GET.get('next', 'homepage')
            return redirect(next_url)
    else:
        form = AuthenticationForm()

    return render(request, 'erickvale/login.html', {'form': form})


def logout_view(request):
    """User logout view."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('homepage')
