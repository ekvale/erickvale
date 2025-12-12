"""
Management command to expand codebook coverage by:
1. Adding more useful codes based on common literary analysis patterns
2. Providing tools to bulk code more segments
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from literary_analysis.models import CodebookTemplate, Code, Analysis, CodedSegment, LiteraryWork


class Command(BaseCommand):
    help = 'Expand codebook with additional codes and help increase code coverage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--add-codes',
            action='store_true',
            help='Add additional useful codes to the codebook',
        )
        parser.add_argument(
            '--analysis-id',
            type=int,
            help='Analysis ID to work with (optional)',
        )
        parser.add_argument(
            '--suggest-segments',
            action='store_true',
            help='Analyze text and suggest segments to code',
        )

    def handle(self, *args, **options):
        # Get the Dhalgren codebook
        try:
            codebook = CodebookTemplate.objects.get(name='Dhalgren - Complete Analysis')
        except CodebookTemplate.DoesNotExist:
            self.stdout.write(self.style.ERROR('Codebook "Dhalgren - Complete Analysis" not found.'))
            return
        
        if options['add_codes']:
            self.add_additional_codes(codebook)
        
        if options['suggest_segments']:
            analysis_id = options.get('analysis_id')
            if not analysis_id:
                # Try to find the Dhalgren analysis
                try:
                    work = LiteraryWork.objects.filter(title__icontains='Dhalgren').first()
                    if work:
                        analysis = Analysis.objects.filter(literary_work=work).first()
                        if analysis:
                            analysis_id = analysis.pk
                except:
                    pass
            
            if analysis_id:
                self.suggest_segments(analysis_id)
            else:
                self.stdout.write(self.style.ERROR('Please provide --analysis-id or ensure a Dhalgren analysis exists.'))

    def add_additional_codes(self, codebook):
        """Add additional useful codes to expand coverage."""
        self.stdout.write('Adding additional codes to expand coverage...\n')
        
        additional_codes = [
            # More specific character interactions
            {
                'name': 'CHARACTER_INTERACTION',
                'type': 'descriptive',
                'definition': 'Interactions between characters',
                'order': 34,
                'parent': 'CHARACTER_ENTITY',
            },
            {
                'name': 'CONFLICT',
                'type': 'descriptive',
                'definition': 'Conflict between characters or forces',
                'order': 35,
                'parent': 'CHARACTER_ENTITY',
            },
            
            # More sensory codes
            {
                'name': 'SOUND',
                'type': 'descriptive',
                'definition': 'Auditory descriptions, sounds, silence',
                'order': 202,
                'parent': None,
            },
            {
                'name': 'TOUCH',
                'type': 'descriptive',
                'definition': 'Tactile descriptions, texture, physical contact',
                'order': 203,
                'parent': None,
            },
            {
                'name': 'SMELL',
                'type': 'descriptive',
                'definition': 'Olfactory descriptions, scents, odors',
                'order': 204,
                'parent': None,
            },
            {
                'name': 'TASTE',
                'type': 'descriptive',
                'definition': 'Gustatory descriptions, flavors',
                'order': 205,
                'parent': None,
            },
            
            # More process codes
            {
                'name': 'COMMUNICATING',
                'type': 'process',
                'definition': 'Characters communicating, talking, sharing information',
                'order': 96,
                'parent': None,
            },
            {
                'name': 'LEARNING',
                'type': 'process',
                'definition': 'Character learning, understanding, gaining knowledge',
                'order': 97,
                'parent': None,
            },
            {
                'name': 'QUESTIONING',
                'type': 'process',
                'definition': 'Asking questions, seeking answers',
                'order': 98,
                'parent': None,
            },
            
            # More structure codes
            {
                'name': 'PARALLEL_STRUCTURE',
                'type': 'structure',
                'definition': 'Parallel scenes, mirrored events',
                'order': 175,
                'parent': None,
            },
            {
                'name': 'FORESHADOWING',
                'type': 'structure',
                'definition': 'Hints at future events',
                'order': 176,
                'parent': None,
            },
            {
                'name': 'IRONY',
                'type': 'structure',
                'definition': 'Irony, contradiction, unexpected outcomes',
                'order': 177,
                'parent': None,
            },
            
            # More emotion codes
            {
                'name': 'LONGING',
                'type': 'emotion',
                'definition': 'Longing, yearning, desire for something absent',
                'order': 113,
                'parent': None,
            },
            {
                'name': 'NOSTALGIA',
                'type': 'emotion',
                'definition': 'Nostalgia, wistfulness for the past',
                'order': 114,
                'parent': None,
            },
            {
                'name': 'WONDER',
                'type': 'emotion',
                'definition': 'Wonder, awe, amazement',
                'order': 115,
                'parent': None,
            },
            
            # More setting codes
            {
                'name': 'WEATHER',
                'type': 'descriptive',
                'definition': 'Weather conditions, atmospheric descriptions',
                'order': 10,
                'parent': None,
            },
            {
                'name': 'NIGHT_DAY',
                'type': 'descriptive',
                'definition': 'Time of day, day/night cycles',
                'order': 11,
                'parent': None,
            },
            {
                'name': 'INTERIOR_EXTERIOR',
                'type': 'descriptive',
                'definition': 'Indoor vs outdoor spaces',
                'order': 12,
                'parent': None,
            },
            
            # More object codes
            {
                'name': 'CLOTHING',
                'type': 'descriptive',
                'definition': 'Clothing, garments, dress',
                'order': 46,
                'parent': 'OBJECT_ENTITY',
            },
            {
                'name': 'FOOD',
                'type': 'descriptive',
                'definition': 'Food, eating, meals',
                'order': 47,
                'parent': 'OBJECT_ENTITY',
            },
            {
                'name': 'BODY',
                'type': 'descriptive',
                'definition': 'Body parts, physical descriptions of bodies',
                'order': 48,
                'parent': 'OBJECT_ENTITY',
            },
            
            # More specific Dhalgren codes
            {
                'name': 'BELLONA_TIMES',
                'type': 'descriptive',
                'definition': 'References to the Bellona Times newspaper',
                'order': 13,
                'parent': None,
            },
            {
                'name': 'MOON',
                'type': 'descriptive',
                'definition': 'References to the moon, lunar imagery',
                'order': 14,
                'parent': None,
            },
            {
                'name': 'DREAMS',
                'type': 'descriptive',
                'definition': 'Dreams, dream-like states, visions',
                'order': 15,
                'parent': None,
            },
            {
                'name': 'MUSIC',
                'type': 'descriptive',
                'definition': 'Music, sound, rhythm, musical references',
                'order': 16,
                'parent': None,
            },
            {
                'name': 'DANCE',
                'type': 'descriptive',
                'definition': 'Dancing, movement, choreography',
                'order': 17,
                'parent': None,
            },
            {
                'name': 'RITUAL',
                'type': 'descriptive',
                'definition': 'Rituals, ceremonies, formalized actions',
                'order': 18,
                'parent': None,
            },
            {
                'name': 'MYTHOLOGY',
                'type': 'descriptive',
                'definition': 'Mythological references, archetypal patterns',
                'order': 19,
                'parent': None,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for code_data in additional_codes:
            parent_code = None
            if code_data.get('parent'):
                try:
                    parent_code = Code.objects.get(codebook=codebook, code_name=code_data['parent'])
                except Code.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'  ⚠ Parent code "{code_data["parent"]}" not found for {code_data["name"]}'))
            
            code, created = Code.objects.get_or_create(
                codebook=codebook,
                code_name=code_data['name'],
                defaults={
                    'code_type': code_data['type'],
                    'definition': code_data['definition'],
                    'order': code_data['order'],
                    'parent_code': parent_code,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Created {code_data["name"]}')
            else:
                # Update existing
                code.order = code_data['order']
                code.parent_code = parent_code
                code.code_type = code_data['type']
                code.definition = code_data['definition']
                code.save()
                updated_count += 1
                self.stdout.write(f'  ✓ Updated {code_data["name"]}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Added/updated {len(additional_codes)} codes ({created_count} new, {updated_count} updated)'))
        self.stdout.write(f'  Total codes in codebook: {codebook.codes.count()}')

    def suggest_segments(self, analysis_id):
        """Analyze text and suggest segments that might need coding."""
        try:
            analysis = Analysis.objects.get(pk=analysis_id)
        except Analysis.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Analysis {analysis_id} not found.'))
            return
        
        work = analysis.literary_work
        if not work.text_file:
            self.stdout.write(self.style.ERROR('No text file found for this analysis.'))
            return
        
        self.stdout.write(f'\nAnalyzing text for "{work.title}"...')
        self.stdout.write(f'Current coverage: {analysis.coded_segments.count()} segments\n')
        
        # Read the text
        try:
            with open(work.text_file.path, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading text file: {e}'))
            return
        
        # Get existing coded positions
        existing_segments = analysis.coded_segments.all()
        coded_ranges = [(seg.start_position, seg.end_position) for seg in existing_segments]
        
        # Find potential segments to code
        # Look for key phrases, dialogue, descriptive passages
        suggestions = []
        
        # Look for dialogue (quoted text)
        import re
        dialogue_pattern = r'"[^"]{50,500}"'  # Dialogue 50-500 chars
        for match in re.finditer(dialogue_pattern, text):
            start, end = match.span()
            # Check if already coded
            if not any(s <= start < e or s < end <= e for s, e in coded_ranges):
                suggestions.append({
                    'start': start,
                    'end': end,
                    'text': match.group()[:100] + '...',
                    'reason': 'Dialogue',
                })
        
        # Look for descriptive passages (long sentences with sensory words)
        sensory_words = ['saw', 'heard', 'felt', 'smelled', 'tasted', 'looked', 'sounded', 'felt like']
        sentences = re.split(r'[.!?]\s+', text)
        current_pos = 0
        for sentence in sentences:
            if len(sentence) > 100 and any(word in sentence.lower() for word in sensory_words):
                start = text.find(sentence, current_pos)
                if start != -1:
                    end = start + len(sentence)
                    # Check if already coded
                    if not any(s <= start < e or s < end <= e for s, e in coded_ranges):
                        suggestions.append({
                            'start': start,
                            'end': end,
                            'text': sentence[:100] + '...',
                            'reason': 'Sensory description',
                        })
                    current_pos = start + len(sentence)
        
        self.stdout.write(f'Found {len(suggestions)} potential segments to code:\n')
        for i, sug in enumerate(suggestions[:20], 1):  # Show first 20
            self.stdout.write(f'  {i}. [{sug["start"]}-{sug["end"]}] {sug["reason"]}: {sug["text"]}')
        
        if len(suggestions) > 20:
            self.stdout.write(f'  ... and {len(suggestions) - 20} more')
        
        self.stdout.write(f'\n💡 Tip: Use the coding interface to code these segments.')
        self.stdout.write(f'   Visit: /apps/literary/analyses/{analysis_id}/code/')

