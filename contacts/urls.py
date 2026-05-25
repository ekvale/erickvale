from django.urls import path

from . import views

app_name = 'contacts'

urlpatterns = [
    path('', views.ContactListView.as_view(), name='list'),
    path('import/', views.contact_import_page, name='import'),
    path('<int:pk>/', views.ContactDetailView.as_view(), name='detail'),
    path('add/', views.ContactCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.ContactUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ContactDeleteView.as_view(), name='delete'),
    path('import/gmail/', views.import_gmail_contacts_view, name='import_gmail'),
    path('import/file/', views.import_file_contacts, name='import_file'),
]
