"""
Management command to load complete Dhalgren analysis from JSON.
"""
import json
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.core.files import File
from django.utils import timezone
from literary_analysis.models import (
    LiteraryWork, CodebookTemplate, Code, Analysis, CodedSegment, AnalyticalMemo
)


class Command(BaseCommand):
    help = 'Load complete Dhalgren analysis from JSON file'

    def handle(self, *args, **options):
        # Get or create a superuser
        try:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.create_user('admin', 'admin@example.com', 'admin')
                user.is_superuser = True
                user.is_staff = True
                user.save()
        except:
            user = User.objects.first()
        
        if not user:
            self.stdout.write(self.style.ERROR('No user found. Please create a user first.'))
            return
        
        # Load JSON file
        json_path = os.path.join(settings.BASE_DIR, 'literary_analysis', 'data', 'dhalgren_analysis.json')
        # Try authoritative clean version first, fall back to regular
        text_path = os.path.join(settings.BASE_DIR, 'literary_analysis', 'data', 'dhalgren_authoritative_clean.txt')
        if not os.path.exists(text_path):
            text_path = os.path.join(settings.BASE_DIR, 'literary_analysis', 'data', 'dhalgren.txt')
        
        if not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR(f'JSON file not found: {json_path}'))
            return
        
        if not os.path.exists(text_path):
            self.stdout.write(self.style.ERROR(f'Text file not found: {text_path}'))
            return
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 1. Create or get LiteraryWork
        text_data = data.get('text', {})
        work, created = LiteraryWork.objects.update_or_create(
            title=text_data.get('title', 'Dhalgren'),
            author=text_data.get('author', 'Samuel R. Delany'),
            defaults={
                'uploaded_by': user,
            }
        )
        
        # Upload/update text file with clean version
        with open(text_path, 'rb') as f:
            work.text_file.save('dhalgren.txt', File(f), save=False)
        
        # Calculate text length
        try:
            with work.text_file.open('r', encoding='utf-8') as f:
                text = f.read()
                work.text_length = len(text)
                work.save()
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not calculate text length: {e}'))
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created literary work: {work.title}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Using existing work: {work.title}'))
        
        # 2. Load codebook (reuse existing command logic)
        codebook_data = data.get('codebook', {})
        codebook_name = codebook_data.get('name', 'Dhalgren - Complete Analysis')
        
        codebook, created = CodebookTemplate.objects.update_or_create(
            name=codebook_name,
            template_type='dhalgren',
            defaults={
                'description': 'Pre-built codebook for analyzing Samuel R. Delany\'s Dhalgren. Includes codes for urban apocalypse, identity & sexuality, artistic creation, and narrative structure.',
                'is_public': True,
                'created_by': user,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created codebook: {codebook.name}'))
            # Clear existing codes
            codebook.codes.all().delete()
        else:
            self.stdout.write(self.style.SUCCESS(f'Using existing codebook: {codebook.name}'))
            codebook.codes.all().delete()
        
        # Load codes
        codes_data = codebook_data.get('codes', [])
        code_map = {}
        
        for code_data in codes_data:
            code_name = code_data.get('name')
            code_type = code_data.get('type', 'descriptive')
            definition = code_data.get('definition', '')
            examples = code_data.get('examples', [])
            parent_name = code_data.get('parent')
            
            parent_code = None
            if parent_name and parent_name in code_map:
                parent_code = code_map[parent_name]
            
            code, _ = Code.objects.get_or_create(
                codebook=codebook,
                code_name=code_name,
                defaults={
                    'code_type': code_type,
                    'definition': definition,
                    'examples': examples,
                    'parent_code': parent_code,
                }
            )
            
            code.code_type = code_type
            code.definition = definition
            code.examples = examples
            code.parent_code = parent_code
            code.save()
            
            code_map[code_name] = code
        
        self.stdout.write(self.style.SUCCESS(f'Loaded {len(codes_data)} codes'))
        
        # 3. Create Analysis
        analysis, created = Analysis.objects.get_or_create(
            literary_work=work,
            codebook=codebook,
            analyst=user,
            defaults={}
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created analysis'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Using existing analysis'))
            # Clear existing segments and memos
            analysis.coded_segments.all().delete()
            analysis.memos.all().delete()
        
        # 4. Load coded segments
        segments_data = data.get('coded_segments', [])
        segment_count = 0
        
        for seg_data in segments_data:
            text_excerpt = seg_data.get('text', '')
            location = seg_data.get('location', '')
            memo = seg_data.get('memo', '')
            code_names = seg_data.get('codes', [])
            
            # Parse location to get positions (e.g., "Pos 0-500")
            start_pos = 0
            end_pos = len(text_excerpt)
            
            if location and 'Pos' in location:
                try:
                    pos_part = location.split('Pos')[1].strip()
                    if '-' in pos_part:
                        start_pos, end_pos = map(int, pos_part.split('-'))
                except:
                    pass
            
            # Try to find the text in the full text to get accurate positions
            try:
                with work.text_file.open('r', encoding='utf-8') as f:
                    full_text = f.read()
                    # Find the segment in the full text
                    text_start = full_text.find(text_excerpt[:100])  # Find first 100 chars
                    if text_start != -1:
                        start_pos = text_start
                        end_pos = text_start + len(text_excerpt)
            except:
                pass
            
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
            for code_name in code_names:
                if code_name in code_map:
                    segment.codes.add(code_map[code_name])
            
            segment_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Loaded {segment_count} coded segments'))
        
        # 5. Load memos
        memos_data = data.get('memos', [])
        memo_count = 0
        
        for memo_data in memos_data:
            AnalyticalMemo.objects.create(
                analysis=analysis,
                title=memo_data.get('title', ''),
                content=memo_data.get('content', ''),
                created_by=user
            )
            memo_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Loaded {memo_count} analytical memos'))
        
        # 6. Store JSON data in analysis
        analysis.json_data = data
        analysis.save()
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully loaded complete Dhalgren analysis!'))
        self.stdout.write(self.style.SUCCESS(f'  Work: {work.title}'))
        self.stdout.write(self.style.SUCCESS(f'  Codebook: {codebook.name} ({len(codes_data)} codes)'))
        self.stdout.write(self.style.SUCCESS(f'  Segments: {segment_count}'))
        self.stdout.write(self.style.SUCCESS(f'  Memos: {memo_count}'))
        self.stdout.write(self.style.SUCCESS(f'\n  Analysis ID: {analysis.pk}'))
        self.stdout.write(self.style.SUCCESS(f'  View at: /apps/literary/analyses/{analysis.pk}/'))

