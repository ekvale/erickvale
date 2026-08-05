import logging

from django.db.models.signals import m2m_changed, post_migrate, post_save
from django.dispatch import receiver

from .models import Publication
from .permissions import bootstrap_publication_groups

logger = logging.getLogger(__name__)


@receiver(post_migrate)
def ensure_publication_groups(sender, **kwargs):
    if sender.name != "mdh_publications":
        return

    bootstrap_publication_groups()


@receiver(post_migrate)
def sync_facets_from_tags_on_migrate(sender, **kwargs):
    if sender.name == "mdh_publications":
        for publication in Publication.objects.prefetch_related("tags"):
            publication.facets.set(publication.tags.values_list("facet", flat=True).distinct())


@receiver(m2m_changed, sender=Publication.tags.through)
def sync_facets_from_tags(sender, instance, action, **kwargs):
    if action in {"post_add", "post_remove", "post_clear"}:
        instance.facets.set(instance.tags.values_list("facet", flat=True).distinct())


_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp"}


def _extract_from_pdf(file_field):
    from pypdf import PdfReader

    with file_field.open("rb") as f:
        reader = PdfReader(f)
        pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def _extract_from_image(file_field):
    import pytesseract
    from django.conf import settings
    from PIL import Image

    tesseract_cmd = getattr(settings, "TESSERACT_CMD", None)
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    with file_field.open("rb") as f:
        image = Image.open(f)
        image.load()  # read into memory before the file handle closes
    return pytesseract.image_to_string(image).strip()


@receiver(post_save, sender=Publication)
def extract_file_text(sender, instance, **kwargs):
    """Extract searchable text from an uploaded PDF or image and store it in pdf_text."""
    if not instance.file_upload:
        return

    ext = ""
    name = instance.file_upload.name or ""
    if "." in name:
        ext = name.rsplit(".", 1)[-1].lower()
        ext = f".{ext}"

    try:
        if ext == ".pdf":
            extracted = _extract_from_pdf(instance.file_upload)
        elif ext in _IMAGE_EXTENSIONS:
            extracted = _extract_from_image(instance.file_upload)
        else:
            return
    except Exception:
        logger.exception("File text extraction failed for publication pk=%s", instance.pk)
        return

    if extracted == instance.pdf_text:
        return

    Publication.objects.filter(pk=instance.pk).update(pdf_text=extracted)