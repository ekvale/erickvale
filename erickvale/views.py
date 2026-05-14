from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from braindump.authz import braindump_configured, is_braindump_owner


def homepage(request):
    """Public landing page (HTAC-focused)."""
    if (
        request.user.is_authenticated
        and braindump_configured()
        and is_braindump_owner(request.user)
    ):
        return redirect('braindump:dashboard')
    return render(request, 'erickvale/homepage.html')


def about(request):
    """About page view."""
    return render(request, 'erickvale/about.html')


def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        if braindump_configured() and is_braindump_owner(request.user):
            return redirect('braindump:dashboard')
        return redirect('homepage')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next', 'homepage')
            if (
                braindump_configured()
                and is_braindump_owner(user)
                and next_url == 'homepage'
            ):
                return redirect('braindump:dashboard')
            return redirect(next_url)
    else:
        form = AuthenticationForm()
    
    return render(request, 'erickvale/login.html', {'form': form})


def logout_view(request):
    """User logout view."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('homepage')

