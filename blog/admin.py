from django.contrib import admin
from .models import Post, Category, Tag, Comment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'publish_date', 'featured', 'views']
    list_filter = ['status', 'publish_date', 'category', 'tags', 'featured']
    search_fields = ['title', 'content', 'excerpt']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'publish_date'
    filter_horizontal = ['tags']
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'author', 'content', 'excerpt', 'featured_image'),
            'classes': ('wide',),
        }),
        ('Categorization', {
            'fields': ('category', 'tags')
        }),
        ('Publishing', {
            'fields': ('status', 'publish_date', 'featured')
        }),
        ('Statistics', {
            'fields': ('views',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Auto-set author to current user if not set."""
        if not change:  # Only for new posts
            obj.author = request.user
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        """Make author read-only after creation."""
        if obj:  # Editing an existing post
            return ['author']
        return []
    
    class Media:
        css = {
            'all': ('ckeditor/ckeditor.css',)
        }


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author_name', 'post', 'created_at', 'approved']
    list_filter = ['approved', 'created_at']
    search_fields = ['author_name', 'author_email', 'content']
    date_hierarchy = 'created_at'
    actions = ['approve_comments']
    
    def approve_comments(self, request, queryset):
        queryset.update(approved=True)
    approve_comments.short_description = 'Approve selected comments'
