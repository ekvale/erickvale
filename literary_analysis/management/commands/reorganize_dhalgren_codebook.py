"""
Management command to reorganize Dhalgren codebook based on best practices.
Creates hierarchical structure, adds missing codes, and reorders everything logically.
"""
from django.core.management.base import BaseCommand
from literary_analysis.models import CodebookTemplate, Code


class Command(BaseCommand):
    help = 'Reorganize Dhalgren codebook with hierarchical structure and logical ordering'

    def handle(self, *args, **options):
        # Get the Dhalgren codebook
        try:
            codebook = CodebookTemplate.objects.get(name='Dhalgren - Complete Analysis')
        except CodebookTemplate.DoesNotExist:
            self.stdout.write(self.style.ERROR('Codebook "Dhalgren - Complete Analysis" not found.'))
            return
        
        self.stdout.write(self.style.SUCCESS('Starting codebook reorganization...\n'))
        
        # Step 1: Create parent codes for major categories
        self.stdout.write('Step 1: Creating parent codes...')
        parent_codes = self.create_parent_codes(codebook)
        
        # Step 2: Reorganize existing codes with hierarchy and new order
        self.stdout.write('\nStep 2: Reorganizing existing codes...')
        self.reorganize_codes(codebook, parent_codes)
        
        # Step 3: Add missing character name codes
        self.stdout.write('\nStep 3: Adding missing character codes...')
        self.add_character_codes(codebook, parent_codes['CHARACTER_ENTITY'])
        
        self.stdout.write(self.style.SUCCESS('\n✓ Codebook reorganization complete!'))
        self.stdout.write(f'  Total codes: {codebook.codes.count()}')
        self.stdout.write(f'  Parent codes: {Code.objects.filter(codebook=codebook, parent_code__isnull=True).count()}')
        self.stdout.write(f'  Subcodes: {Code.objects.filter(codebook=codebook, parent_code__isnull=False).count()}')

    def create_parent_codes(self, codebook):
        """Create parent codes for major categories."""
        parents = {}
        
        parent_definitions = {
            'CHARACTER_ENTITY': {
                'code_type': 'descriptive',
                'definition': 'Parent code for all character-related codes (names, roles, identity)',
                'order': 20,
            },
            'OBJECT_ENTITY': {
                'code_type': 'descriptive',
                'definition': 'Parent code for all object and symbol codes',
                'order': 40,
            },
            'SOCIAL_ENTITY': {
                'code_type': 'descriptive',
                'definition': 'Parent code for all social structure codes',
                'order': 60,
            },
        }
        
        for parent_name, attrs in parent_definitions.items():
            parent, created = Code.objects.get_or_create(
                codebook=codebook,
                code_name=parent_name,
                defaults={
                    'code_type': attrs['code_type'],
                    'definition': attrs['definition'],
                    'order': attrs['order'],
                    'parent_code': None,
                }
            )
            if not created:
                # Update existing
                parent.code_type = attrs['code_type']
                parent.definition = attrs['definition']
                parent.order = attrs['order']
                parent.save()
            
            parents[parent_name] = parent
            self.stdout.write(f'  ✓ {parent_name}')
        
        return parents

    def reorganize_codes(self, codebook, parent_codes):
        """Reorganize all existing codes with proper hierarchy and ordering."""
        
        # Define the new organization structure
        # Format: code_name: (order, parent_code_key, code_type)
        reorganization = {
            # SETTING & SPACE (0-19)
            'BELLONA_CITY': (0, None, 'descriptive'),
            'ARCHITECTURE': (1, None, 'descriptive'),
            'SPATIAL_DISORIENTATION': (2, None, 'descriptive'),
            'URBAN_DECAY': (3, None, 'descriptive'),
            'FIRE_DESTRUCTION': (4, None, 'descriptive'),
            'THRESHOLD': (5, None, 'descriptive'),
            'LABYRINTH': (6, None, 'descriptive'),
            'UNDERWORLD_DESCENT': (7, None, 'descriptive'),
            'TWILIGHT_DAWN': (8, None, 'descriptive'),
            'CARNIVAL': (9, None, 'descriptive'),
            
            # CHARACTER ROLES (under CHARACTER_ENTITY, 25-28)
            'TRICKSTER': (25, 'CHARACTER_ENTITY', 'descriptive'),
            'ORACLE_PROPHET': (26, 'CHARACTER_ENTITY', 'descriptive'),
            'MENTOR_GUIDE': (27, 'CHARACTER_ENTITY', 'descriptive'),
            'HOMELESS_DRIFTER': (28, 'CHARACTER_ENTITY', 'descriptive'),
            
            # CHARACTER IDENTITY (under CHARACTER_ENTITY, 29-33)
            'OUTSIDER_STATUS': (29, 'CHARACTER_ENTITY', 'descriptive'),
            'NAME_AMNESIA': (30, 'CHARACTER_ENTITY', 'descriptive'),
            'IDENTITY_FLUID': (31, 'CHARACTER_ENTITY', 'descriptive'),
            'RACIAL_DYNAMICS': (32, 'CHARACTER_ENTITY', 'descriptive'),
            'CLASS_PRIVILEGE': (33, 'CHARACTER_ENTITY', 'descriptive'),
            
            # OBJECTS & SYMBOLS (under OBJECT_ENTITY, 40-45)
            'NOTEBOOK': (40, 'OBJECT_ENTITY', 'descriptive'),
            'ORCHID_CHAINS': (41, 'OBJECT_ENTITY', 'descriptive'),
            'OPTICAL_CHAIN': (42, 'OBJECT_ENTITY', 'descriptive'),
            'WEAPON': (43, 'OBJECT_ENTITY', 'descriptive'),
            'LIGHT_SOURCE': (44, 'OBJECT_ENTITY', 'descriptive'),
            'REFLECTION_MIRROR': (45, 'OBJECT_ENTITY', 'descriptive'),
            
            # SOCIAL STRUCTURES (under SOCIAL_ENTITY, 60-65)
            'SCORPIONS_GANG': (60, 'SOCIAL_ENTITY', 'descriptive'),
            'COMMUNE_LIFE': (61, 'SOCIAL_ENTITY', 'descriptive'),
            'ALTERNATIVE_FAMILY': (62, 'SOCIAL_ENTITY', 'descriptive'),
            'TRIBAL_IDENTITY': (63, 'SOCIAL_ENTITY', 'descriptive'),
            'ARTISTIC_CIRCLE': (64, 'SOCIAL_ENTITY', 'descriptive'),
            'SOCIAL_COLLAPSE': (65, 'SOCIAL_ENTITY', 'descriptive'),
            
            # PROCESSES & ACTIONS (80-95)
            'WANDERING': (80, None, 'process'),
            'SEARCHING': (81, None, 'process'),
            'SURVIVAL': (82, None, 'process'),
            'SELF_CREATION': (83, None, 'process'),
            'TRANSFORMING': (84, None, 'process'),
            'REBIRTH_RENEWAL': (85, None, 'process'),
            'MUTUAL_AID': (86, None, 'process'),
            'RESISTING': (87, None, 'process'),
            'WRITING_PROCESS': (88, None, 'process'),
            'CREATION_ACT': (89, None, 'process'),
            'CREATING': (90, None, 'process'),
            'POETRY_PERFORMANCE': (91, None, 'process'),
            'OBSERVING': (92, None, 'process'),
            'REMEMBERING': (93, None, 'process'),
            'FRAGMENTING': (94, None, 'process'),
            'DISSOLVING': (95, None, 'process'),
            
            # EMOTIONS (100-112)
            'FEAR': (100, None, 'emotion'),
            'PARANOIA': (101, None, 'emotion'),  # Will set parent to FEAR below
            'ANGER': (102, None, 'emotion'),
            'SADNESS': (103, None, 'emotion'),
            'ALIENATION': (104, None, 'emotion'),  # Will set parent to SADNESS below
            'DESPAIR': (105, None, 'emotion'),  # Will set parent to SADNESS below
            'SHAME': (106, None, 'emotion'),  # Will set parent to SADNESS below
            'JOY': (107, None, 'emotion'),
            'ECSTASY': (108, None, 'emotion'),  # Will set parent to JOY below
            'DISGUST': (109, None, 'emotion'),
            'CONFUSION': (110, None, 'emotion'),
            'ISOLATION': (111, None, 'emotion'),
            'INTIMACY': (112, None, 'emotion'),
            
            # RELATIONSHIPS & DESIRE (120-125)
            'QUEER_DESIRE': (120, None, 'descriptive'),
            'POLYAMORY': (121, None, 'descriptive'),
            'SEXUAL_ENCOUNTER': (122, None, 'descriptive'),
            'GENDER_PLAY': (123, None, 'descriptive'),
            'DOMINANCE_SUBMISSION': (124, None, 'descriptive'),
            'VIOLENCE_DESIRE': (125, None, 'descriptive'),
            
            # REALITY & TIME (140-143)
            'TEMPORAL_ANOMALY': (140, None, 'descriptive'),
            'TEMPORAL_CONFUSION': (141, None, 'structure'),
            'REALITY_BREAK': (142, None, 'descriptive'),
            'MEMORY_LOSS': (143, None, 'descriptive'),
            
            # NARRATIVE STRUCTURE (160-174)
            'CIRCULAR_STRUCTURE': (160, None, 'structure'),
            'FRAGMENTATION': (161, None, 'structure'),
            'METAFICTION': (162, None, 'structure'),
            'TYPOGRAPHIC_PLAY': (163, None, 'structure'),
            'MULTIPLE_PERSPECTIVES': (164, None, 'structure'),
            'STREAM_CONSCIOUSNESS': (165, None, 'structure'),
            'REPETITION_VARIATION': (166, None, 'structure'),
            'PROLEPSIS': (167, None, 'structure'),
            'ANALEPSIS': (168, None, 'structure'),
            'UNRELIABLE_NARRATION': (169, None, 'structure'),
            'READER_ADDRESS': (170, None, 'structure'),
            'TEXTUAL_ARTIFACT': (171, None, 'structure'),
            'HERO_JOURNEY': (172, None, 'structure'),
            'TEMPORAL_SHIFT': (173, None, 'descriptive'),
            'PERSPECTIVE_SHIFT': (174, None, 'descriptive'),
            
            # NARRATIVE ELEMENTS (180-185)
            'SETTING': (180, None, 'descriptive'),
            'CHARACTER': (181, None, 'descriptive'),
            'DIALOGUE': (182, None, 'descriptive'),
            'INTERIOR_MONOLOGUE': (183, None, 'descriptive'),
            'NARRATIVE_VOICE': (184, None, 'descriptive'),
            'SYMBOLISM': (185, None, 'descriptive'),
            
            # SENSORY & PERCEPTUAL (200-201)
            'SENSORY_DETAIL': (200, None, 'descriptive'),
            'OPTICAL_DISTORTION': (201, None, 'descriptive'),
            
            # VALUES (220-228)
            'AUTONOMY': (220, None, 'values'),
            'COMMUNITY': (221, None, 'values'),
            'ORDER': (222, None, 'values'),
            'CHAOS': (223, None, 'values'),
            'TRUTH': (224, None, 'values'),
            'BEAUTY': (225, None, 'values'),
            'POWER': (226, None, 'values'),
            'JUSTICE': (227, None, 'values'),
            'AESTHETIC_JUDGMENT': (228, None, 'process'),
            
            # SOCIAL DYNAMICS (240)
            'EXPLOITATION': (240, None, 'descriptive'),
        }
        
        updated_count = 0
        for code_name, (order, parent_key, code_type) in reorganization.items():
            try:
                code = Code.objects.get(codebook=codebook, code_name=code_name)
                parent = parent_codes.get(parent_key) if parent_key else None
                
                code.order = order
                code.parent_code = parent
                code.code_type = code_type
                code.save()
                updated_count += 1
                
                parent_str = f" (parent: {parent_key})" if parent_key else ""
                self.stdout.write(f'  ✓ {code_name}: order={order}, type={code_type}{parent_str}')
            except Code.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  ⚠ Code "{code_name}" not found, skipping'))
        
        # Set emotion subcode parents
        emotion_parents = {
            'PARANOIA': 'FEAR',
            'ALIENATION': 'SADNESS',
            'DESPAIR': 'SADNESS',
            'SHAME': 'SADNESS',
            'ECSTASY': 'JOY',
        }
        
        for subcode_name, parent_name in emotion_parents.items():
            try:
                subcode = Code.objects.get(codebook=codebook, code_name=subcode_name)
                parent = Code.objects.get(codebook=codebook, code_name=parent_name)
                subcode.parent_code = parent
                subcode.save()
                self.stdout.write(f'  ✓ {subcode_name}: parent set to {parent_name}')
            except Code.DoesNotExist:
                pass
        
        self.stdout.write(f'\n  Updated {updated_count} codes')

    def add_character_codes(self, codebook, character_parent):
        """Add missing character name codes."""
        character_codes = {
            'KID': {
                'order': 20,
                'definition': 'The Kid - protagonist',
            },
            'TAK': {
                'order': 21,
                'definition': 'Tak - character',
            },
            'DENNY': {
                'order': 22,
                'definition': 'Denny - character',
            },
            'LOPP': {
                'order': 23,
                'definition': 'Lopp - character',
            },
            'GEORGE': {
                'order': 24,
                'definition': 'George - character',
            },
        }
        
        created_count = 0
        for char_name, attrs in character_codes.items():
            code, created = Code.objects.get_or_create(
                codebook=codebook,
                code_name=char_name,
                defaults={
                    'code_type': 'descriptive',
                    'definition': attrs['definition'],
                    'order': attrs['order'],
                    'parent_code': character_parent,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Created {char_name}')
            else:
                # Update existing
                code.order = attrs['order']
                code.parent_code = character_parent
                code.code_type = 'descriptive'
                code.definition = attrs['definition']
                code.save()
                self.stdout.write(f'  ✓ Updated {char_name}')
        
        self.stdout.write(f'\n  Processed {len(character_codes)} character codes ({created_count} new)')



