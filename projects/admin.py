from django.contrib import admin

from .models import (
    Comment,
    Contact,
    Document,
    Event,
    Notification,
    Project,
    ProjectMembership,
    Task,
)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'priority', 'owner', 'due_date', 'created_at')
    list_filter = ('status', 'priority', 'created_at')
    search_fields = ('name', 'description')
    raw_id_fields = ('owner',)


@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'role', 'joined_at')
    list_filter = ('role',)
    search_fields = ('project__name', 'user__username')
    raw_id_fields = ('project', 'user')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'priority', 'due_date', 'created_by', 'created_at')
    list_filter = ('status', 'priority', 'project')
    search_fields = ('title', 'description')
    raw_id_fields = ('project', 'parent_task', 'created_by')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'created_at')
    search_fields = ('body', 'task__title')
    raw_id_fields = ('task', 'author')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'task', 'contact', 'uploaded_by', 'file_size', 'created_at')
    search_fields = ('title',)
    raw_id_fields = ('project', 'task', 'contact', 'uploaded_by')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'organization', 'contact_type', 'email', 'created_at')
    list_filter = ('contact_type',)
    search_fields = ('first_name', 'last_name', 'organization', 'email')
    raw_id_fields = ('added_by',)
    filter_horizontal = ('projects',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'project', 'start_datetime', 'end_datetime', 'created_by')
    list_filter = ('event_type',)
    search_fields = ('title', 'description')
    raw_id_fields = ('project', 'task', 'created_by')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'verb', 'actor', 'is_read', 'created_at')
    list_filter = ('is_read',)
    search_fields = ('verb',)
    raw_id_fields = ('recipient', 'actor', 'target_task', 'target_project')
