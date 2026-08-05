import itertools

from django import forms
from django.template.defaultfilters import slugify

from .models import AccessRequest, Facet, Publication, Tag, TopicGroup


class PublicationForm(forms.ModelForm):
    publication_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    class Meta:
        model = Publication
        fields = [
            "title",
            "summary",
            "abstract",
            "document_type",
            "publication_date",
            "source_url",
            "file_upload",
            "status",
            "is_featured",
            "facets",
            "tags",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "summary": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "abstract": forms.Textarea(attrs={"class": "form-control", "rows": 6}),
            "document_type": forms.Select(attrs={"class": "form-control"}),
            "source_url": forms.URLInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "facets": forms.SelectMultiple(attrs={"class": "form-control", "size": 8}),
            "tags": forms.SelectMultiple(attrs={"class": "form-control", "size": 12}),
        }

    def clean(self):
        cleaned_data = super().clean()
        selected_facets = set(cleaned_data.get("facets") or [])
        selected_tags = cleaned_data.get("tags") or []

        for tag in selected_tags:
            selected_facets.add(tag.facet)

        cleaned_data["facets"] = list(selected_facets)
        return cleaned_data


class PublicationFilterForm(forms.Form):
    q = forms.CharField(required=False)
    facet = forms.CharField(required=False)
    tag = forms.CharField(required=False)
    document_type = forms.CharField(required=False)


class FacetForm(forms.ModelForm):
    class Meta:
        model = Facet
        fields = ["code", "name", "description", "sort_order"]
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class TopicGroupForm(forms.ModelForm):
    class Meta:
        model = TopicGroup
        fields = ["facet", "name", "description"]
        widgets = {
            "facet": forms.Select(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.slug:
            base_slug = slugify(obj.name) or "group"
            for index in itertools.count(1):
                candidate = base_slug if index == 1 else f"{base_slug}-{index}"
                if not TopicGroup.objects.filter(facet=obj.facet, slug=candidate).exclude(pk=obj.pk).exists():
                    obj.slug = candidate
                    break
        if commit:
            obj.save()
        return obj


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ["topic_group", "name", "description"]
        widgets = {
            "topic_group": forms.Select(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["topic_group"].queryset = TopicGroup.objects.select_related("facet").order_by(
            "facet__sort_order", "facet__code", "name"
        )
        self.fields["topic_group"].label_from_instance = lambda obj: f"{obj.facet.code} — {obj.name}"

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.facet = obj.topic_group.facet
        if not obj.slug:
            base_slug = slugify(obj.name) or "tag"
            for index in itertools.count(1):
                candidate = base_slug if index == 1 else f"{base_slug}-{index}"
                if not Tag.objects.filter(slug=candidate).exclude(pk=obj.pk).exists():
                    obj.slug = candidate
                    break
        if commit:
            obj.save()
        return obj


class AccessRequestForm(forms.ModelForm):
    class Meta:
        model = AccessRequest
        fields = ["name", "email", "request_type", "reason"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Your full name"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "your.email@example.com"}),
            "request_type": forms.Select(attrs={"class": "form-control"}),
            "reason": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Please describe your request or suggestion…",
                }
            ),
        }
        labels = {
            "email": "Email (optional)",
        }