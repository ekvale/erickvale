"""Staff export of the live facet/tag vocabulary."""

import csv
import io
import zipfile
from datetime import date
from xml.sax.saxutils import escape

from django.db.models import Count
from django.http import HttpResponse
from django.utils.http import content_disposition_header

from .models import Facet, Tag

FACET_HEADERS = [
    "facet_code",
    "facet_name",
    "description",
    "sort_order",
    "topic_group_count",
    "tag_count",
]

TAG_HEADERS = [
    "facet_code",
    "facet_name",
    "topic_group",
    "tag_slug",
    "tag_name",
    "description",
    "publication_count",
]


def _facets_queryset():
    return Facet.objects.annotate(
        topic_group_count=Count("topic_groups", distinct=True),
        tag_count=Count("tags", distinct=True),
    ).order_by("sort_order", "code")


def _tags_queryset():
    return (
        Tag.objects.select_related("facet", "topic_group")
        .annotate(publication_count=Count("publications", distinct=True))
        .order_by("facet__sort_order", "topic_group__name", "name")
    )


def facet_rows():
    rows = [FACET_HEADERS]
    for facet in _facets_queryset():
        rows.append(
            [
                facet.code,
                facet.name,
                facet.description,
                facet.sort_order,
                facet.topic_group_count,
                facet.tag_count,
            ]
        )
    return rows


def tag_rows():
    rows = [TAG_HEADERS]
    for tag in _tags_queryset():
        rows.append(
            [
                tag.facet.code,
                tag.facet.name,
                tag.topic_group.name,
                tag.slug,
                tag.name,
                tag.description,
                tag.publication_count,
            ]
        )
    return rows


def _csv_bytes(rows):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerows(rows)
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


def csv_file_response(filename, rows):
    response = HttpResponse(_csv_bytes(rows), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = content_disposition_header("attachment", filename)
    return response


def csv_zip_response():
    stamp = date.today().isoformat()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"mdh-facets-{stamp}.csv", _csv_bytes(facet_rows()))
        archive.writestr(f"mdh-tags-{stamp}.csv", _csv_bytes(tag_rows()))
    filename = f"mdh-taxonomy-{stamp}.zip"
    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = content_disposition_header("attachment", filename)
    return response


def _sheet_xml(rows):
    lines = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
        "<sheetData>",
    ]
    for row_index, row in enumerate(rows, start=1):
        lines.append(f'<row r="{row_index}">')
        for col_index, value in enumerate(row):
            col = _column_letter(col_index)
            text = escape(str(value if value is not None else ""), {"'": "&apos;"})
            lines.append(
                f'<c r="{col}{row_index}" t="inlineStr"><is><t xml:space="preserve">{text}</t></is></c>'
            )
        lines.append("</row>")
    lines.append("</sheetData></worksheet>")
    return "".join(lines)


def _column_letter(index):
    letter = ""
    index += 1
    while index:
        index, remainder = divmod(index - 1, 26)
        letter = chr(65 + remainder) + letter
    return letter


def xlsx_response():
    stamp = date.today().isoformat()
    buffer = io.BytesIO()
    sheets = {
        "xl/worksheets/sheet1.xml": _sheet_xml(facet_rows()),
        "xl/worksheets/sheet2.xml": _sheet_xml(tag_rows()),
    }
    content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>
"""
    rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>
"""
    workbook = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Facets" sheetId="1" r:id="rId1"/>
    <sheet name="Tags" sheetId="2" r:id="rId2"/>
  </sheets>
</workbook>
"""
    workbook_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>
</Relationships>
"""
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        for path, xml in sheets.items():
            archive.writestr(path, xml)

    filename = f"mdh-taxonomy-{stamp}.xlsx"
    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = content_disposition_header("attachment", filename)
    return response
