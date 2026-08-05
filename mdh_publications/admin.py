from django.contrib import admin

from .models import DocumentType, Facet, LandingImage, Publication, Tag, TopicGroup


@admin.register(Facet)
class FacetAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "sort_order")
    search_fields = ("code", "name", "description")
    ordering = ("sort_order", "code")


@admin.register(TopicGroup)
class TopicGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "facet", "slug")
    list_filter = ("facet",)
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "facet", "topic_group", "slug")
    list_filter = ("facet", "topic_group")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(LandingImage)
class LandingImageAdmin(admin.ModelAdmin):
    list_display = ("title", "slot", "sort_order", "is_active", "created_at", "created_by")
    list_filter = ("is_active", "slot")
    search_fields = ("title", "caption", "alt_text")
    list_editable = ("slot", "sort_order", "is_active")


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ("title", "document_type", "status", "publication_date", "is_featured")
    list_filter = ("status", "document_type", "is_featured", "facets", "tags__facet")
    search_fields = ("title", "summary", "abstract", "slug")
    filter_horizontal = ("facets", "tags")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("document_type", "created_by", "updated_by")