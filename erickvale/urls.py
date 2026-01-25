"""
URL configuration for erickvale project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import homepage, about, login_view, logout_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('apps/emergency/', include('emergency_preparedness.urls')),
    path('apps/blog/', include('blog.urls')),
    path('apps/cards/', include('card_maker.urls')),
    path('apps/literary/', include('literary_analysis.urls')),
    path('apps/personality-game/', include('personality_type_game.urls')),
    path('apps/mango-market/', include('mango_market.urls')),
    path('apps/activity-media/', include('activity_media.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('about/', about, name='about'),
    path('', homepage, name='homepage'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
