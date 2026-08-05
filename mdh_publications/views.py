from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView

from .forms import AccessRequestForm, FacetForm, PublicationForm, TagForm, TopicGroupForm
from .models import AccessRequest, DocumentType, Facet, LandingImage, Publication, Tag, TopicGroup
from .permissions import ADMINISTRATOR_GROUP_NAME, EMPLOYEE_GROUP_NAME


class AboutView(FormView):
    template_name = "mdh_publications/about.html"
    form_class = AccessRequestForm

    def get_success_url(self):
        return reverse_lazy("mdh_publications:publication_about")

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Your request has been submitted. We'll follow up if you provided an email.")
        return super().form_valid(form)


class PublicationSuccessUrlMixin:
    def get_success_url(self):
        return reverse_lazy("mdh_publications:publication_detail", kwargs={"slug": self.object.slug})


class PublicationLandingView(TemplateView):
    template_name = "mdh_publications/publication_landing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active = LandingImage.objects.filter(is_active=True)
        context["hero_images"] = active.filter(slot=LandingImage.Slot.HERO)
        context["img_topic"] = active.filter(slot=LandingImage.Slot.BROWSE_TOPIC).first()
        context["img_contributor"] = active.filter(slot=LandingImage.Slot.BROWSE_CONTRIBUTOR).first()
        context["img_format"] = active.filter(slot=LandingImage.Slot.BROWSE_FORMAT).first()
        # Keep for admin gallery section
        context["landing_images"] = LandingImage.objects.all()
        context["facets"] = (
            Facet.objects.prefetch_related("tags", "topic_groups")
            .annotate(pub_count=Count("publications", distinct=True))
            .order_by("sort_order", "code")
        )
        context["featured_publications"] = (
            Publication.objects.filter(is_featured=True, status=Publication.Status.PUBLISHED)
            .select_related("document_type")
            .prefetch_related("tags")[:6]
        )
        context["total_publications"] = Publication.objects.filter(
            status=Publication.Status.PUBLISHED
        ).count()
        context["total_facets"] = Facet.objects.count()
        context["total_document_types"] = DocumentType.objects.filter(is_active=True).count()
        context["document_types"] = DocumentType.objects.filter(is_active=True)
        return context


# ──────────────────────────────────────────────────────────────────────────────
# Landing image management (admin only)
# ──────────────────────────────────────────────────────────────────────────────

class LandingImageAdminMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = "mdh_publications.manage_publication_roles"
    raise_exception = True


class LandingImageListView(LandingImageAdminMixin, ListView):
    model = LandingImage
    template_name = "mdh_publications/landing_image_list.html"
    context_object_name = "landing_images"
    queryset = LandingImage.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["slot_choices"] = LandingImage.Slot.choices
        return context


class LandingImageCreateView(LandingImageAdminMixin, CreateView):
    model = LandingImage
    template_name = "mdh_publications/landing_image_form.html"
    fields = ["slot", "image", "title", "caption", "alt_text", "sort_order", "is_active"]
    success_url = reverse_lazy("mdh_publications:landing_image_list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class LandingImageUpdateView(LandingImageAdminMixin, UpdateView):
    model = LandingImage
    template_name = "mdh_publications/landing_image_form.html"
    fields = ["slot", "image", "title", "caption", "alt_text", "sort_order", "is_active"]
    success_url = reverse_lazy("mdh_publications:landing_image_list")


class LandingImageDeleteView(LandingImageAdminMixin, DeleteView):
    model = LandingImage
    template_name = "mdh_publications/landing_image_confirm_delete.html"
    success_url = reverse_lazy("mdh_publications:landing_image_list")


class PublicationListView(ListView):
    model = Publication
    template_name = "mdh_publications/publication_list.html"
    context_object_name = "publications"
    paginate_by = 25

    def get_queryset(self):
        queryset = (
            Publication.objects.filter(status=Publication.Status.PUBLISHED)
            .select_related("document_type", "created_by")
            .prefetch_related("facets", "tags", "tags__facet", "tags__topic_group")
        )

        query = self.request.GET.get("q", "").strip()
        facet_code = self.request.GET.get("facet", "").strip()
        tag_slugs = self.request.GET.getlist("tag")
        document_type_id = self.request.GET.get("document_type", "").strip()
        pub_date_from = self.request.GET.get("pub_date_from", "").strip()
        pub_date_to = self.request.GET.get("pub_date_to", "").strip()

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(abstract__icontains=query)
                | Q(tags__name__icontains=query)
                | Q(pdf_text__icontains=query)
            )

        if facet_code:
            queryset = queryset.filter(Q(facets__code=facet_code) | Q(tags__facet__code=facet_code))

        if tag_slugs:
            queryset = queryset.filter(tags__slug__in=tag_slugs)

        if document_type_id:
            queryset = queryset.filter(document_type_id=document_type_id)

        if pub_date_from:
            queryset = queryset.filter(publication_date__gte=pub_date_from)

        if pub_date_to:
            queryset = queryset.filter(publication_date__lte=pub_date_to)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["facets"] = Facet.objects.prefetch_related("topic_groups", "tags")
        selected_facet = self.request.GET.get("facet", "")

        tag_queryset = Tag.objects.select_related("facet", "topic_group").order_by(
            "facet__sort_order", "topic_group__name", "name"
        )
        if selected_facet:
            tag_queryset = tag_queryset.filter(facet__code=selected_facet)

        context["filter_tags"] = tag_queryset
        context["selected_facet"] = self.request.GET.get("facet", "")
        context["selected_tags"] = self.request.GET.getlist("tag")
        context["selected_document_type"] = self.request.GET.get("document_type", "")
        context["selected_pub_date_from"] = self.request.GET.get("pub_date_from", "")
        context["selected_pub_date_to"] = self.request.GET.get("pub_date_to", "")
        context["query"] = self.request.GET.get("q", "")
        context["document_types"] = DocumentType.objects.filter(is_active=True)
        return context


class PublicationDetailView(DetailView):
    model = Publication
    template_name = "mdh_publications/publication_detail.html"
    context_object_name = "publication"
    slug_field = "slug"
    slug_url_kwarg = "slug"


class PublicationFormUserMixin:
    """Hand the request user to PublicationForm so it can gate status choices."""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class PublicationCreateView(
    PublicationFormUserMixin,
    PublicationSuccessUrlMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    CreateView,
):
    model = Publication
    permission_required = "mdh_publications.add_publication"
    raise_exception = True
    form_class = PublicationForm
    template_name = "mdh_publications/publication_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class PublicationReviewActionView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Approve, send back, or archive a publication from the admin dashboard.

    The publish_publication permission was declared on the model but never
    enforced anywhere, and nothing in the UI moved a publication out of
    In Review, so submissions had no route to being published.
    """

    permission_required = "mdh_publications.publish_publication"
    raise_exception = True

    ACTIONS = {
        "publish": (Publication.Status.PUBLISHED, "published"),
        "send_back": (Publication.Status.DRAFT, "sent back to the author as a draft"),
        "archive": (Publication.Status.ARCHIVED, "archived"),
    }

    def post(self, request, slug, *args, **kwargs):
        publication = get_object_or_404(Publication, slug=slug)
        action = request.POST.get("action", "")

        if action not in self.ACTIONS:
            messages.error(request, "Unknown review action.")
            return redirect("mdh_publications:publication_admin_dashboard")

        new_status, phrase = self.ACTIONS[action]
        publication.status = new_status
        publication.updated_by = request.user
        publication.save(update_fields=["status", "updated_by", "updated_at"])

        messages.success(request, f"“{publication.title}” was {phrase}.")
        return redirect(
            request.POST.get("next")
            or reverse_lazy("mdh_publications:publication_admin_dashboard")
        )


class PublicationSubmitForReviewView(LoginRequiredMixin, View):
    """Let an author move their own draft into the review queue."""

    def post(self, request, slug, *args, **kwargs):
        publication = get_object_or_404(Publication, slug=slug)

        may_submit = publication.created_by_id == request.user.id or request.user.has_perm(
            "mdh_publications.change_publication"
        )
        if not may_submit:
            raise PermissionDenied("You can only submit publications you created.")

        if publication.status != Publication.Status.DRAFT:
            messages.info(request, f"“{publication.title}” is not a draft.")
        else:
            publication.status = Publication.Status.IN_REVIEW
            publication.updated_by = request.user
            publication.save(update_fields=["status", "updated_by", "updated_at"])
            messages.success(
                request, f"“{publication.title}” was submitted for review."
            )

        return redirect("mdh_publications:publication_employee_dashboard")


class PublicationUpdateView(
    PublicationFormUserMixin,
    PublicationSuccessUrlMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    model = Publication
    permission_required = "mdh_publications.change_publication"
    raise_exception = True
    form_class = PublicationForm
    template_name = "mdh_publications/publication_form.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class PublicationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Publication
    permission_required = "mdh_publications.delete_publication"
    raise_exception = True
    template_name = "mdh_publications/publication_confirm_delete.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"
    success_url = reverse_lazy("mdh_publications:publication_list")


class TaxonomyBrowserView(TemplateView):
    template_name = "mdh_publications/taxonomy_browser.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["facets"] = Facet.objects.prefetch_related("topic_groups__tags")
        context["facet_count"] = Facet.objects.count()
        context["tag_count"] = Tag.objects.count()
        return context


def can_use_review_dashboard(user):
    """Editors and administrators both need the review queue.

    Routing on manage_publication_roles alone sent anyone who could approve
    submissions but not administer users to the employee dashboard, which has
    no review queue -- so their approval permission was unreachable.
    """
    return (
        user.has_perm("mdh_publications.publish_publication")
        or user.has_perm("mdh_publications.manage_publication_taxonomy")
        or user.has_perm("mdh_publications.manage_publication_roles")
    )


class DashboardRouterView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        if can_use_review_dashboard(request.user):
            return redirect("mdh_publications:publication_admin_dashboard")
        return redirect("mdh_publications:publication_employee_dashboard")


class EmployeeDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "mdh_publications/employee_dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["my_recent_publications"] = Publication.objects.filter(created_by=self.request.user).order_by("-created_at")[:10]
        context["total_publications"] = Publication.objects.count()
        context["my_publication_count"] = Publication.objects.filter(created_by=self.request.user).count()
        context["can_add_publication"] = self.request.user.has_perm("mdh_publications.add_publication")
        return context


class AdminDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    raise_exception = True
    template_name = "mdh_publications/admin_dashboard.html"

    def has_permission(self):
        """Editors reach this page too; the role-management card is hidden
        from them in the template and refused in post() below."""
        return can_use_review_dashboard(self.request.user)

    def post(self, request, *args, **kwargs):
        # Everything this handler does -- resolving access requests and moving
        # users between groups -- is administrator work.
        if not request.user.has_perm("mdh_publications.manage_publication_roles"):
            raise PermissionDenied("Managing roles and requests requires an administrator.")

        if "resolve_request_id" in request.POST:
            req = get_object_or_404(AccessRequest, id=request.POST["resolve_request_id"])
            req.is_resolved = True
            req.save()
            messages.success(request, f"Request from {req.name} marked as resolved.")
            return redirect("mdh_publications:publication_admin_dashboard")

        role = request.POST.get("role")
        user_id = request.POST.get("user_id")
        user = get_object_or_404(User, id=user_id)

        if user == request.user and role not in {"admin", "employee"}:
            messages.error(request, "You cannot remove your own administrative access.")
            return redirect("mdh_publications:publication_admin_dashboard")

        employee_group = self._ensure_group(EMPLOYEE_GROUP_NAME)
        admin_group = self._ensure_group(ADMINISTRATOR_GROUP_NAME)

        user.groups.remove(employee_group, admin_group)
        if role == "employee":
            user.groups.add(employee_group)
            messages.success(request, f"{user.username} is now an MDH Publications Employee.")
        elif role == "admin":
            user.groups.add(admin_group)
            messages.success(request, f"{user.username} is now an MDH Publications Administrator.")
        else:
            messages.success(request, f"{user.username} now has public-only access.")

        return redirect("mdh_publications:publication_admin_dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = User.objects.order_by("username").prefetch_related("groups")
        user_rows = []
        for user in users:
            group_names = set(user.groups.values_list("name", flat=True))
            if ADMINISTRATOR_GROUP_NAME in group_names:
                current_role = "Administrator"
                selected_role = "admin"
            elif EMPLOYEE_GROUP_NAME in group_names:
                current_role = "Employee"
                selected_role = "employee"
            else:
                current_role = "Public"
                selected_role = "public"

            user_rows.append(
                {
                    "user": user,
                    "current_role": current_role,
                    "selected_role": selected_role,
                }
            )

        context["user_rows"] = user_rows
        context["total_publications"] = Publication.objects.count()
        context["recently_published"] = Publication.objects.filter(
            status=Publication.Status.PUBLISHED
        ).order_by("-publication_date")[:10]
        context["ready_for_review"] = Publication.objects.filter(
            status=Publication.Status.IN_REVIEW
        ).order_by("-created_at")[:10]
        context["landing_images"] = LandingImage.objects.all()
        context["slot_choices"] = LandingImage.Slot.choices
        context["access_requests"] = AccessRequest.objects.filter(is_resolved=False).order_by("-submitted_at")
        return context

    @staticmethod
    def _ensure_group(name):
        from django.contrib.auth.models import Group

        group, _ = Group.objects.get_or_create(name=name)
        return group


# ──────────────────────────────────────────────────────────────────────────────
# Taxonomy management (admin only)
# ──────────────────────────────────────────────────────────────────────────────

class TaxonomyAdminMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = "mdh_publications.manage_publication_taxonomy"
    raise_exception = True


class TaxonomyManageView(TaxonomyAdminMixin, TemplateView):
    template_name = "mdh_publications/taxonomy_manage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["facets"] = Facet.objects.prefetch_related(
            "topic_groups__tags"
        ).order_by("sort_order", "code")
        return context


class FacetCreateView(TaxonomyAdminMixin, CreateView):
    model = Facet
    form_class = FacetForm
    template_name = "mdh_publications/facet_form.html"
    success_url = reverse_lazy("mdh_publications:taxonomy_manage")


class FacetUpdateView(TaxonomyAdminMixin, UpdateView):
    model = Facet
    form_class = FacetForm
    template_name = "mdh_publications/facet_form.html"
    success_url = reverse_lazy("mdh_publications:taxonomy_manage")


class FacetDeleteView(TaxonomyAdminMixin, DeleteView):
    model = Facet
    template_name = "mdh_publications/facet_confirm_delete.html"
    success_url = reverse_lazy("mdh_publications:taxonomy_manage")


class TopicGroupCreateView(TaxonomyAdminMixin, CreateView):
    model = TopicGroup
    form_class = TopicGroupForm
    template_name = "mdh_publications/topic_group_form.html"
    success_url = reverse_lazy("mdh_publications:taxonomy_manage")

    def get_initial(self):
        initial = super().get_initial()
        facet_pk = self.request.GET.get("facet")
        if facet_pk:
            try:
                initial["facet"] = Facet.objects.get(pk=facet_pk)
            except (Facet.DoesNotExist, ValueError):
                pass
        return initial


class TopicGroupUpdateView(TaxonomyAdminMixin, UpdateView):
    model = TopicGroup
    form_class = TopicGroupForm
    template_name = "mdh_publications/topic_group_form.html"
    success_url = reverse_lazy("mdh_publications:taxonomy_manage")


class TopicGroupDeleteView(TaxonomyAdminMixin, DeleteView):
    model = TopicGroup
    template_name = "mdh_publications/topic_group_confirm_delete.html"
    success_url = reverse_lazy("mdh_publications:taxonomy_manage")


class TagCreateView(TaxonomyAdminMixin, CreateView):
    model = Tag
    form_class = TagForm
    template_name = "mdh_publications/tag_form.html"
    success_url = reverse_lazy("mdh_publications:taxonomy_manage")

    def get_initial(self):
        initial = super().get_initial()
        tg_pk = self.request.GET.get("topic_group")
        if tg_pk:
            try:
                initial["topic_group"] = TopicGroup.objects.get(pk=tg_pk)
            except (TopicGroup.DoesNotExist, ValueError):
                pass
        return initial


class TagUpdateView(TaxonomyAdminMixin, UpdateView):
    model = Tag
    form_class = TagForm
    template_name = "mdh_publications/tag_form.html"
    success_url = reverse_lazy("mdh_publications:taxonomy_manage")


class TagDeleteView(TaxonomyAdminMixin, DeleteView):
    model = Tag
    template_name = "mdh_publications/tag_confirm_delete.html"
    success_url = reverse_lazy("mdh_publications:taxonomy_manage")
