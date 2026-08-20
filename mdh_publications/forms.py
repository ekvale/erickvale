import itertools

from django import forms
from django.core.validators import FileExtensionValidator
from django.template.defaultfilters import slugify

from .models import (
    ACCEPTED_UPLOAD_EXTENSIONS,
    DESCRIPTION_MIN_LENGTH,
    AccessRequest,
    DocumentType,
    Facet,
    Publication,
    Tag,
    TagConstellationItem,
    TopicGroup,
)


class PublicationForm(forms.ModelForm):
    publication_date = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        help_text="Date the publication was issued or last substantially revised.",
    )
    description = forms.CharField(
        required=True,
        min_length=DESCRIPTION_MIN_LENGTH,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 6,
                "data-min-length": DESCRIPTION_MIN_LENGTH,
            }
        ),
        help_text=(
            f"Required. Dublin Core description of what the document is. "
            f"Minimum {DESCRIPTION_MIN_LENGTH} characters. Do not use a separate "
            "summary or abstract."
        ),
    )
    document_type = forms.ModelChoiceField(
        queryset=DocumentType.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
        help_text="Required. Choose the controlled document type that best fits.",
    )
    language = forms.ChoiceField(
        choices=Publication._meta.get_field("language").choices,
        required=True,
        widget=forms.Select(attrs={"class": "form-control"}),
        help_text=(
            "Language of this file. A Hmong translation of a TB fact sheet should "
            "be tagged Tuberculosis, with language Hmong — not a Hmong ethnicity tag "
            "unless the content is about that community."
        ),
    )
    source_url = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={"class": "form-control"}),
        help_text=(
            "Public web page for this publication (for example on health.mn.gov). "
            "Provide a source URL, a file upload, or both. At least one is required."
        ),
    )
    file_upload = forms.FileField(
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=ACCEPTED_UPLOAD_EXTENSIONS)],
        help_text=(
            "Accepted types: PDF, DOCX, XLSX, CSV, PPTX, PNG, JPG. "
            "Name files without spaces: YYYY-MM-DD_short-title_language_v1.pdf "
            "(NNLM file naming conventions)."
        ),
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.select_related("facet", "topic_group"),
        required=True,
        widget=forms.SelectMultiple(attrs={"class": "form-control", "size": 12}),
        help_text="Required. Tag what the document is about, not the language it is written in.",
    )

    class Meta:
        model = Publication
        fields = [
            "title",
            "description",
            "document_type",
            "publication_date",
            "language",
            "is_translated",
            "source_url",
            "file_upload",
            "status",
            "is_featured",
            "tags",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "is_translated": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_featured": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "is_translated": "Translated document",
            "is_featured": "Featured on landing page",
        }
        help_texts = {
            "title": "Required. Use the document's official title.",
            "is_translated": (
                "Check if this file is a translation. Pair with the correct "
                "Publication Language. Do not add a race/ethnicity tag solely because "
                "the file is translated."
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        """Restrict status and featured to what ``user`` is allowed to set."""
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["title"].required = True
        self.fields["document_type"].label_from_instance = self._document_type_label

        can_steward = user is not None and user.has_perm("mdh_publications.publish_publication")
        if not can_steward:
            self.fields.pop("is_featured", None)
            allowed = {Publication.Status.DRAFT, Publication.Status.IN_REVIEW}
            if self.instance and self.instance.pk:
                allowed.add(self.instance.status)
            self.fields["status"].choices = [
                (value, label)
                for value, label in Publication.Status.choices
                if value in allowed
            ]
            self.fields["status"].help_text = (
                "Choose In Review to submit this for a library steward to publish. "
                "Featured status is set by stewards after review."
            )

    @staticmethod
    def _document_type_label(obj):
        if obj.scope_note:
            note = obj.scope_note[:80] + ("…" if len(obj.scope_note) > 80 else "")
            return f"{obj.name} — {note}"
        return obj.name

    def clean_status(self):
        status = self.cleaned_data.get("status")
        user = getattr(self, "user", None)
        restricted = {Publication.Status.PUBLISHED, Publication.Status.ARCHIVED}
        if (
            user is not None
            and status in restricted
            and not user.has_perm("mdh_publications.publish_publication")
            and not (self.instance and self.instance.pk and self.instance.status == status)
        ):
            raise forms.ValidationError(
                "You do not have permission to publish or archive. "
                "Choose In Review to submit it for approval."
            )
        return status

    def clean_description(self):
        description = (self.cleaned_data.get("description") or "").strip()
        if len(description) < DESCRIPTION_MIN_LENGTH:
            raise forms.ValidationError(
                f"Description must be at least {DESCRIPTION_MIN_LENGTH} characters "
                f"(currently {len(description)})."
            )
        return description

    def clean(self):
        cleaned_data = super().clean()
        source_url = (cleaned_data.get("source_url") or "").strip()
        upload = cleaned_data.get("file_upload")
        existing_file = self.instance and self.instance.pk and self.instance.file_upload
        if not source_url and not upload and not existing_file:
            raise forms.ValidationError(
                "Provide a source URL, a file upload, or both. At least one is required."
            )

        selected_tags = cleaned_data.get("tags") or []
        cleaned_data["facets"] = list({tag.facet for tag in selected_tags})
        return cleaned_data

    def save(self, commit=True):
        obj = super().save(commit=False)
        if commit:
            obj.save()
            self.save_m2m()
            facets = self.cleaned_data.get("facets") or []
            obj.facets.set(facets)
        return obj


class PublicationFilterForm(forms.Form):
    q = forms.CharField(required=False)
    facet = forms.CharField(required=False)
    tag = forms.CharField(required=False)
    document_type = forms.CharField(required=False)
    language = forms.CharField(required=False)


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


class TagConstellationItemForm(forms.ModelForm):
    class Meta:
        model = TagConstellationItem
        fields = ["kind", "title", "note", "url", "publication", "sort_order"]
        widgets = {
            "kind": forms.Select(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "url": forms.URLInput(attrs={"class": "form-control"}),
            "publication": forms.Select(attrs={"class": "form-control"}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control", "style": "max-width:6rem"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["publication"].queryset = Publication.objects.order_by("title")
        self.fields["publication"].required = False
        self.fields["note"].required = False
        self.fields["url"].required = False


TagConstellationItemFormSet = forms.inlineformset_factory(
    Tag,
    TagConstellationItem,
    form=TagConstellationItemForm,
    extra=3,
    can_delete=True,
)


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
