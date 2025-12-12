"""
Management command to load codes from Dhalgren analysis JSON into codebook.
"""
import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from literary_analysis.models import CodebookTemplate, Code
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Load codes from Dhalgren analysis JSON into codebook'

    def handle(self, *args, **options):
        # Get or create a user
        user = User.objects.filter(is_superuser=True).first()
        if not user:
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

        # Get or create codebook
        codebook_data = data.get('codebook', {})
        codebook_name = codebook_data.get('name', 'Dhalgren - Complete Analysis')
        
        codebook, created = CodebookTemplate.objects.get_or_create(
            name=codebook_name,
            defaults={
                'template_type': 'dhalgren',
                'description': 'Pre-built codebook for analyzing Samuel R. Delany\'s Dhalgren. Includes codes for urban apocalypse, identity & sexuality, artistic creation, and narrative structure.',
                'is_public': True,
                'created_by': user,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created codebook: {codebook.name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Using existing codebook: {codebook.name}'))

        # Load codes
        codes_data = codebook_data.get('codes', [])
        codes_created = 0
        codes_updated = 0
        
        for idx, code_data in enumerate(codes_data):
            code_name = code_data.get('name', '')
            if not code_name:
                continue
                
            code_type = code_data.get('type', 'descriptive')
            definition = code_data.get('definition', '')
            examples = code_data.get('examples', [])
            parent_name = code_data.get('parent')
            
            # Find parent code if specified
            parent_code = None
            if parent_name:
                try:
                    parent_code = Code.objects.get(codebook=codebook, code_name=parent_name)
                except Code.DoesNotExist:
                    pass
            
            code, created = Code.objects.update_or_create(
                codebook=codebook,
                code_name=code_name,
                defaults={
                    'code_type': code_type,
                    'definition': definition,
                    'examples': examples,
                    'parent_code': parent_code,
                    'order': idx,
                }
            )
            
            if created:
                codes_created += 1
            else:
                codes_updated += 1

        self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully loaded codes!'))
        self.stdout.write(self.style.SUCCESS(f'  Created: {codes_created}'))
        self.stdout.write(self.style.SUCCESS(f'  Updated: {codes_updated}'))
        self.stdout.write(self.style.SUCCESS(f'  Total codes in codebook: {codebook.codes.count()}'))

