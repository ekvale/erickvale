"""
Management command to load Dhalgren codebook template from JSON.
"""
import json
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from literary_analysis.models import CodebookTemplate, Code


class Command(BaseCommand):
    help = 'Load Dhalgren codebook template from JSON file'

    def handle(self, *args, **options):
        # Get or create a superuser for the codebook
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
        
        if not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR(f'JSON file not found: {json_path}'))
            return
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create or get codebook template
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
        else:
            self.stdout.write(self.style.SUCCESS(f'Using existing codebook: {codebook.name}'))
            # Clear existing codes
            codebook.codes.all().delete()
        
        # Load codes
        codes_data = codebook_data.get('codes', [])
        code_map = {}  # Map code names to Code objects for parent relationships
        
        for code_data in codes_data:
            code_name = code_data.get('name')
            code_type = code_data.get('type', 'descriptive')
            definition = code_data.get('definition', '')
            examples = code_data.get('examples', [])
            parent_name = code_data.get('parent')
            
            # Get parent code if specified
            parent_code = None
            if parent_name and parent_name in code_map:
                parent_code = code_map[parent_name]
            
            code, code_created = Code.objects.get_or_create(
                codebook=codebook,
                code_name=code_name,
                defaults={
                    'code_type': code_type,
                    'definition': definition,
                    'examples': examples,
                    'parent_code': parent_code,
                }
            )
            
            code_map[code_name] = code
            
            if code_created:
                self.stdout.write(f'  Created code: {code_name}')
            else:
                # Update existing code
                code.code_type = code_type
                code.definition = definition
                code.examples = examples
                code.parent_code = parent_code
                code.save()
                self.stdout.write(f'  Updated code: {code_name}')
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully loaded {len(codes_data)} codes into codebook!'))

