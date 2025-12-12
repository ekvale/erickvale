"""
Utility functions for literary analysis app.
"""
from django.http import JsonResponse
import json
import csv
from io import StringIO


def export_analysis_csv(analysis):
    """Export analysis data to CSV format."""
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Segment ID', 'Start Position', 'End Position', 'Text Excerpt', 'Codes', 'Location', 'Memo', 'Created At'])
    
    # Segments
    for segment in analysis.coded_segments.all().order_by('start_position'):
        codes = ', '.join([code.code_name for code in segment.codes.all()])
        writer.writerow([
            segment.pk,
            segment.start_position,
            segment.end_position,
            segment.text_excerpt[:500],  # Limit length
            codes,
            segment.location,
            segment.memo,
            segment.created_at.isoformat()
        ])
    
    return output.getvalue()


def export_analysis_json(analysis):
    """Export analysis data to JSON format."""
    data = {
        'analysis_id': analysis.pk,
        'literary_work': {
            'title': analysis.literary_work.title,
            'author': analysis.literary_work.author,
        },
        'codebook': {
            'name': analysis.codebook.name,
            'description': analysis.codebook.description,
        },
        'codes': [],
        'segments': [],
        'memos': []
    }
    
    # Codes
    for code in analysis.codebook.codes.all():
        data['codes'].append({
            'name': code.code_name,
            'type': code.code_type,
            'definition': code.definition,
            'examples': code.examples,
        })
    
    # Segments
    for segment in analysis.coded_segments.all().order_by('start_position'):
        data['segments'].append({
            'id': segment.pk,
            'start_position': segment.start_position,
            'end_position': segment.end_position,
            'text_excerpt': segment.text_excerpt,
            'codes': [code.code_name for code in segment.codes.all()],
            'location': segment.location,
            'memo': segment.memo,
            'created_at': segment.created_at.isoformat(),
        })
    
    # Memos
    for memo in analysis.memos.all():
        data['memos'].append({
            'title': memo.title,
            'content': memo.content,
            'created_at': memo.created_at.isoformat(),
        })
    
    return json.dumps(data, indent=2, ensure_ascii=False)


def validate_segment_positions(start_pos, end_pos, max_length):
    """Validate segment positions."""
    errors = []
    
    if start_pos < 0:
        errors.append('Start position must be non-negative')
    
    if end_pos < 0:
        errors.append('End position must be non-negative')
    
    if start_pos >= end_pos:
        errors.append('Start position must be less than end position')
    
    if end_pos > max_length:
        errors.append(f'End position ({end_pos}) exceeds text length ({max_length})')
    
    if end_pos - start_pos > 10000:  # Reasonable limit
        errors.append('Segment is too long (maximum 10,000 characters)')
    
    return errors

