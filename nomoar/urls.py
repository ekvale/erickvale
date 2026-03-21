from django.urls import path

from . import views
from .feeds import LatestEventsFeed

app_name = 'nomoar'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('Timeline/', views.TimelineView.as_view(), name='timeline'),
    path('Map/', views.MapView.as_view(), name='map'),
    path('EventDetail/<slug:slug>/', views.EventDetailView.as_view(), name='event_detail'),
    path(
        'api/event/<slug:slug>/fist/',
        views.toggle_event_fist,
        name='toggle_event_fist',
    ),
    path('Submit/', views.submit_event, name='submit'),
    path('Educators/', views.EducatorsView.as_view(), name='educators'),
    path(
        'Educators/subscribe/',
        views.subscribe_educator_newsletter,
        name='educator_subscribe',
    ),
    path('Pricing/', views.PricingView.as_view(), name='pricing'),
    path('paths/', views.LearningPathListView.as_view(), name='learning_path_list'),
    path('paths/<slug:slug>/', views.LearningPathDetailView.as_view(), name='learning_path_detail'),
    path('collections/', views.CollectionListView.as_view(), name='collection_list'),
    path(
        'collections/<slug:slug>/',
        views.CollectionDetailView.as_view(),
        name='collection_detail',
    ),
    path('lesson-kits/', views.LessonKitListView.as_view(), name='lesson_kit_list'),
    path(
        'lesson-kits/<slug:slug>/',
        views.LessonKitDetailView.as_view(),
        name='lesson_kit_detail',
    ),
    path('whats-new/', views.WhatsNewView.as_view(), name='whats_new'),
    path('glossary/', views.GlossaryListView.as_view(), name='glossary_list'),
    path(
        'glossary/<slug:slug>/',
        views.GlossaryTermDetailView.as_view(),
        name='glossary_term_detail',
    ),
    path('places/', views.PlaceIndexView.as_view(), name='place_index'),
    path('commentary/', views.NewsPostListView.as_view(), name='news_post_list'),
    path(
        'commentary/<slug:slug>/',
        views.NewsPostDetailView.as_view(),
        name='news_post_detail',
    ),
    path('packs/', views.ResourcePackListView.as_view(), name='resource_pack_list'),
    path(
        'packs/<slug:slug>/',
        views.ResourcePackDetailView.as_view(),
        name='resource_pack_detail',
    ),
    path('Heroes/', views.HeroesView.as_view(), name='heroes'),
    path('HeroDetail/<slug:slug>/', views.HeroDetailView.as_view(), name='hero_detail'),
    path('feed/events.xml', LatestEventsFeed(), name='events_feed_rss'),
    path('feed/events.json', views.events_feed_json, name='events_feed_json'),
    path('oembed/', views.oembed, name='oembed'),
    path('Embed/Event/<slug:slug>/', views.embed_event, name='embed_event'),
    path('Embed/slice/', views.embed_slice, name='embed_slice'),
]
