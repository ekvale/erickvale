from django.contrib import admin

from .models import Contact


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'email', 'phone', 'source', 'birthday', 'company')
    list_filter = ('source',)
    search_fields = ('first_name', 'last_name', 'display_name', 'email', 'company')
    filter_horizontal = ('projects', 'tasks')
