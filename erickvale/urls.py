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
from .views import about, contact, coming_soon, homepage, login_view, logout_view, services

from htac.views_admin import about as htac_admin_about
from htac.views_public import (
    HTACAboutView,
    PipelineStep1View,
    PipelineStep2View,
    PipelineStep3View,
    PipelineStep4View,
    PipelineStep5View,
    PipelineStep6View,
    PipelineStep7View,
)
from htac.views_pipeline_demo import (
    pipeline_demo,
    pipeline_reset,
    pipeline_run_start,
    pipeline_run_status,
)

urlpatterns = [
    path('admin/htac/about/', htac_admin_about, name='htac_about'),
    path('admin/', admin.site.urls),
    path('apps/emergency/', include('emergency_preparedness.urls')),
    path('apps/blog/', include('blog.urls')),
    path('apps/cards/', include('card_maker.urls')),
    path('apps/literary/', include('literary_analysis.urls')),
    path('apps/personality-game/', include('personality_type_game.urls')),
    path('apps/mango-market/', include('mango_market.urls')),
    path('apps/activity-media/', include('activity_media.urls')),
    path('apps/fraud-detection/', include('fraud_detection.urls')),
    path('apps/human-rights-archive/', include('human_rights_archive.urls')),
    path('apps/allminnesota/', include('allminnesota.urls')),
    path('apps/arm-chair-detective/', include('arm_chair_detective.urls')),
    path('chess/', include('chess_trainer.urls')),
    path('apps/nomoar/', include('nomoar.urls')),
    path('apps/dream-blue/', include('dream_blue.urls')),
    path('apps/braindump/', include('braindump.urls')),
    path('apps/contacts/', include('contacts.urls', namespace='contacts')),
    path('mdh/', include('mdh_briefings.urls')),
    path('htac/about/', HTACAboutView.as_view(), name='htac_public_about'),
    path('htac/demo/', pipeline_demo, name='htac_pipeline_demo'),
    path('htac/demo/run/', pipeline_run_start, name='htac_pipeline_run_start'),
    path('htac/demo/status/<int:run_id>/', pipeline_run_status, name='htac_pipeline_run_status'),
    path('htac/demo/reset/', pipeline_reset, name='htac_pipeline_reset'),
    path('htac/pipeline/1/', PipelineStep1View.as_view(), name='htac_pipeline_step1'),
    path('htac/pipeline/2/', PipelineStep2View.as_view(), name='htac_pipeline_step2'),
    path('htac/pipeline/3/', PipelineStep3View.as_view(), name='htac_pipeline_step3'),
    path('htac/pipeline/4/', PipelineStep4View.as_view(), name='htac_pipeline_step4'),
    path('htac/pipeline/5/', PipelineStep5View.as_view(), name='htac_pipeline_step5'),
    path('htac/pipeline/6/', PipelineStep6View.as_view(), name='htac_pipeline_step6'),
    path('htac/pipeline/7/', PipelineStep7View.as_view(), name='htac_pipeline_step7'),
    path('api/htac/v1/', include('htac.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('coming-soon/', coming_soon, name='coming_soon'),
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('services/', services, name='services'),
    # Project management (projects, contacts, calendar, notifications — see projects.urls)
    path('', include('projects.urls')),
    path('', homepage, name='homepage'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
