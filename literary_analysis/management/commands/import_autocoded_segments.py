"""
Management command to import autocoded segments from JSON file.
Expects a JSON array of segments with: text, location, codes, memo (optional)
"""
import json
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from literary_analysis.models import (
    LiteraryWork, CodebookTemplate, Code, Analysis, CodedSegment
)


class Command(BaseCommand):
    help = 'Import autocoded segments from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='dhalgren_autocoded+segements_full.json',
            help='Path to JSON file with coded segments (default: dhalgren_autocoded+segements_full.json)'
        )
        parser.add_argument(
            '--work-title',
            type=str,
            default='Dhalgren',
            help='Title of the literary work (default: Dhalgren)'
        )
        parser.add_argument(
            '--codebook-name',
            type=str,
            default='Dhalgren - Complete Analysis',
            help='Name of the codebook (default: Dhalgren - Complete Analysis)'
        )
        parser.add_argument(
            '--analysis-name',
            type=str,
            default=None,
            help='Name for the analysis (default: auto-generated)'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing segments before importing (non-interactive)'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        work_title = options['work_title']
        codebook_name = options['codebook_name']
        analysis_name = options['analysis_name'] or f'{work_title} - Autocoded Analysis'
        
        # Get or create user
        try:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.first()
        except:
            user = User.objects.first()
        
        if not user:
            self.stdout.write(self.style.ERROR('No user found. Please create a user first.'))
            return
        
        # Check if file path is absolute or relative
        if not os.path.isabs(file_path):
            # Try root directory first
            json_path = os.path.join(settings.BASE_DIR, file_path)
            if not os.path.exists(json_path):
                # Try data directory
                json_path = os.path.join(settings.BASE_DIR, 'literary_analysis', 'data', file_path)
        else:
            json_path = file_path
        
        if not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR(f'JSON file not found: {json_path}'))
            self.stdout.write(self.style.WARNING(f'Tried: {os.path.join(settings.BASE_DIR, file_path)}'))
            self.stdout.write(self.style.WARNING(f'And: {os.path.join(settings.BASE_DIR, "literary_analysis", "data", file_path)}'))
            return
        
        self.stdout.write(f'Loading segments from: {json_path}')
        
        # Load JSON file
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Invalid JSON file: {e}'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading file: {e}'))
            return
        
        # Handle different JSON structures
        if isinstance(data, list):
            # Direct array of segments
            segments_data = data
        elif isinstance(data, dict):
            # Object with segments array
            segments_data = data.get('coded_segments', data.get('segments', []))
        else:
            self.stdout.write(self.style.ERROR('Invalid JSON structure. Expected array or object with segments array.'))
            return
        
        if not segments_data:
            self.stdout.write(self.style.ERROR('No segments found in JSON file.'))
            return
        
        self.stdout.write(f'Found {len(segments_data)} segments to import')
        
        # Get or create LiteraryWork
        work, created = LiteraryWork.objects.get_or_create(
            title=work_title,
            defaults={
                'author': 'Samuel R. Delany',
                'uploaded_by': user,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created literary work: {work.title}'))
        else:
            self.stdout.write(f'Using existing work: {work.title}')
        
        # Get codebook
        try:
            codebook = CodebookTemplate.objects.get(name=codebook_name)
        except CodebookTemplate.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Codebook "{codebook_name}" not found.'))
            self.stdout.write(self.style.WARNING('Available codebooks:'))
            for cb in CodebookTemplate.objects.all():
                self.stdout.write(f'  - {cb.name}')
            return
        
        self.stdout.write(f'Using codebook: {codebook.name}')
        
        # Create code map
        code_map = {}
        for code in codebook.codes.all():
            code_map[code.code_name] = code
        
        self.stdout.write(f'Found {len(code_map)} codes in codebook')
        
        # Get or create Analysis
        analysis, created = Analysis.objects.get_or_create(
            literary_work=work,
            codebook=codebook,
            defaults={
                'analyst': user,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created analysis: {analysis.pk}'))
        else:
            self.stdout.write(f'Using existing analysis: {analysis.pk}')
            # Clear existing segments if requested or if flag is set
            if options.get('clear_existing'):
                deleted_count = analysis.coded_segments.count()
                analysis.coded_segments.all().delete()
                self.stdout.write(f'Deleted {deleted_count} existing segments')
            elif analysis.coded_segments.exists():
                # Ask if user wants to clear existing segments (only if interactive)
                try:
                    response = input('Analysis already exists. Clear existing segments? (yes/no): ')
                    if response.lower() == 'yes':
                        deleted_count = analysis.coded_segments.count()
                        analysis.coded_segments.all().delete()
                        self.stdout.write(f'Deleted {deleted_count} existing segments')
                except (EOFError, KeyboardInterrupt):
                    self.stdout.write(self.style.WARNING('Keeping existing segments'))
        
        # Get full text for position finding
        full_text = ""
        if work.text_file:
            try:
                with open(work.text_file.path, 'r', encoding='utf-8') as f:
                    full_text = f.read()
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not read text file: {e}'))
        
        # Import segments
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        for idx, segment_data in enumerate(segments_data, 1):
            try:
                text_excerpt = segment_data.get('text', segment_data.get('text_excerpt', ''))
                if not text_excerpt:
                    self.stdout.write(self.style.WARNING(f'Segment {idx}: No text found, skipping'))
                    skipped_count += 1
                    continue
                
                # Handle location - can be string or object
                location_data = segment_data.get('location', '')
                if isinstance(location_data, dict):
                    # Extract from location object
                    location = location_data.get('chapter_or_section', '')
                    if location and location_data.get('start_char') is not None:
                        location += f" (chars {location_data.get('start_char')}-{location_data.get('end_char')})"
                else:
                    location = str(location_data) if location_data else ''
                
                codes = segment_data.get('codes', [])
                memo = segment_data.get('memo', '')
                
                # Get start and end positions - check location object first
                start_pos = None
                end_pos = None
                
                if isinstance(location_data, dict):
                    start_pos = location_data.get('start_char')
                    end_pos = location_data.get('end_char')
                
                # Fall back to direct fields
                if start_pos is None:
                    start_pos = segment_data.get('start_position', segment_data.get('start_pos', None))
                if end_pos is None:
                    end_pos = segment_data.get('end_position', segment_data.get('end_pos', None))
                
                # If positions not provided, try to find text in full text
                if start_pos is None or end_pos is None:
                    if full_text:
                        text_start = full_text.find(text_excerpt[:100])
                        if text_start != -1:
                            start_pos = text_start
                            end_pos = text_start + len(text_excerpt)
                        else:
                            # Try with first 50 chars
                            text_start = full_text.find(text_excerpt[:50])
                            if text_start != -1:
                                start_pos = text_start
                                end_pos = text_start + len(text_excerpt)
                
                # If still no positions, use 0 as fallback
                if start_pos is None:
                    start_pos = 0
                if end_pos is None:
                    end_pos = len(text_excerpt)
                
                # Validate positions
                if end_pos <= start_pos:
                    self.stdout.write(self.style.WARNING(f'Segment {idx}: Invalid positions ({start_pos}-{end_pos}), skipping'))
                    skipped_count += 1
                    continue
                
                # Create segment
                segment = CodedSegment.objects.create(
                    analysis=analysis,
                    start_position=start_pos,
                    end_position=end_pos,
                    text_excerpt=text_excerpt,
                    location=location,
                    memo=memo,
                    created_by=user
                )
                
                # Add codes
                valid_codes = 0
                for code_name in codes:
                    if code_name in code_map:
                        segment.codes.add(code_map[code_name])
                        valid_codes += 1
                    else:
                        self.stdout.write(self.style.WARNING(f'Segment {idx}: Code "{code_name}" not found in codebook'))
                
                if valid_codes == 0:
                    self.stdout.write(self.style.WARNING(f'Segment {idx}: No valid codes found, segment created without codes'))
                
                imported_count += 1
                
                if idx % 100 == 0:
                    self.stdout.write(f'  Processed {idx}/{len(segments_data)} segments...')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Segment {idx}: Error - {e}'))
                error_count += 1
                continue
        
        # Summary
        self.stdout.write(self.style.SUCCESS(f'\n✓ Import complete!'))
        self.stdout.write(f'  Imported: {imported_count}')
        self.stdout.write(f'  Skipped: {skipped_count}')
        self.stdout.write(f'  Errors: {error_count}')
        self.stdout.write(f'\n  Analysis ID: {analysis.pk}')
        self.stdout.write(f'  View at: /apps/literary/analyses/{analysis.pk}/')

