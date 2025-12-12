"""
Management command to expand Dhalgren codebook coverage by:
1. Identifying uncoded text segments
2. Suggesting segments based on key phrases and patterns
3. Optionally auto-coding segments with high confidence matches
"""
import re
import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from literary_analysis.models import Analysis, CodebookTemplate, Code, CodedSegment, LiteraryWork


class Command(BaseCommand):
    help = 'Expand Dhalgren codebook coverage by identifying and coding more segments'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analysis-id',
            type=int,
            help='ID of the analysis to expand',
        )
        parser.add_argument(
            '--auto-code',
            action='store_true',
            help='Automatically code high-confidence matches (use with caution)',
        )
        parser.add_argument(
            '--min-segment-length',
            type=int,
            default=50,
            help='Minimum segment length to consider (default: 50)',
        )
        parser.add_argument(
            '--max-segment-length',
            type=int,
            default=500,
            help='Maximum segment length to consider (default: 500)',
        )
        parser.add_argument(
            '--coverage-target',
            type=float,
            default=30.0,
            help='Target coverage percentage (default: 30.0)',
        )

    def handle(self, *args, **options):
        analysis_id = options.get('analysis_id')
        auto_code = options.get('auto_code', False)
        min_length = options.get('min_segment_length', 50)
        max_length = options.get('max_segment_length', 500)
        target_coverage = options.get('coverage_target', 30.0)
        
        # Get analysis
        if analysis_id:
            try:
                analysis = Analysis.objects.get(pk=analysis_id)
            except Analysis.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Analysis {analysis_id} not found.'))
                return
        else:
            # Try to find Dhalgren analysis
            try:
                work = LiteraryWork.objects.filter(title__icontains='dhalgren').first()
                if not work:
                    self.stdout.write(self.style.ERROR('No Dhalgren analysis found. Please specify --analysis-id'))
                    return
                analysis = Analysis.objects.filter(literary_work=work).first()
                if not analysis:
                    self.stdout.write(self.style.ERROR('No analysis found for Dhalgren. Please create one first.'))
                    return
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error finding analysis: {e}'))
                return
        
        work = analysis.literary_work
        codebook = analysis.codebook
        
        self.stdout.write(self.style.SUCCESS(f'\nExpanding coverage for: {work.title}'))
        self.stdout.write(f'Using codebook: {codebook.name}\n')
        
        # Get current coverage
        current_segments = analysis.coded_segments.all()
        coded_ranges = [(seg.start_position, seg.end_position) for seg in current_segments]
        coded_chars = sum(seg.end_position - seg.start_position for seg in current_segments)
        total_chars = work.text_length or 0
        current_coverage = (coded_chars / total_chars * 100) if total_chars > 0 else 0.0
        
        self.stdout.write(f'Current coverage: {current_coverage:.2f}%')
        self.stdout.write(f'Current segments: {len(current_segments)}')
        self.stdout.write(f'Target coverage: {target_coverage:.2f}%\n')
        
        if current_coverage >= target_coverage:
            self.stdout.write(self.style.SUCCESS('Already at or above target coverage!'))
            return
        
        # Read text
        if not work.text_file:
            self.stdout.write(self.style.ERROR('No text file found.'))
            return
        
        try:
            with open(work.text_file.path, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading text: {e}'))
            return
        
        # Get user
        user = analysis.analyst
        
        # Find uncoded segments with high coding potential
        suggestions = self.find_coding_opportunities(
            text, coded_ranges, codebook, min_length, max_length
        )
        
        self.stdout.write(f'\nFound {len(suggestions)} potential segments to code\n')
        
        # Display top suggestions
        self.stdout.write('Top 20 suggestions:')
        for i, suggestion in enumerate(suggestions[:20], 1):
            self.stdout.write(f'\n{i}. Position {suggestion["start"]}-{suggestion["end"]} ({suggestion["end"]-suggestion["start"]} chars)')
            self.stdout.write(f'   Suggested codes: {", ".join(suggestion["codes"])}')
            self.stdout.write(f'   Reason: {suggestion["reason"]}')
            self.stdout.write(f'   Text preview: {suggestion["text"][:100]}...')
        
        if auto_code:
            self.stdout.write(f'\n\nAuto-coding high-confidence segments...')
            created = self.auto_code_segments(analysis, suggestions, user, min_confidence=0.7)
            self.stdout.write(self.style.SUCCESS(f'Created {created} new coded segments'))
        else:
            self.stdout.write(f'\n\nTo auto-code high-confidence segments, run with --auto-code flag')
            self.stdout.write(f'This will create segments with confidence >= 0.7')
        
        # Calculate new coverage
        new_segments = analysis.coded_segments.all()
        new_coded_chars = sum(seg.end_position - seg.start_position for seg in new_segments)
        new_coverage = (new_coded_chars / total_chars * 100) if total_chars > 0 else 0.0
        
        self.stdout.write(f'\nNew coverage: {new_coverage:.2f}%')
        self.stdout.write(f'New segments: {len(new_segments)}')
        self.stdout.write(f'Coverage increase: {new_coverage - current_coverage:.2f}%')

    def find_coding_opportunities(self, text, coded_ranges, codebook, min_length, max_length):
        """Find text segments that should be coded based on patterns and keywords."""
        suggestions = []
        
        # Get code keywords/phrases for pattern matching
        code_patterns = self.get_code_patterns(codebook)
        
        # Strategy 1: Find dialogue (high value for coding)
        dialogue_suggestions = self.find_dialogue_segments(text, coded_ranges, min_length, max_length)
        suggestions.extend(dialogue_suggestions)
        
        # Strategy 2: Find segments matching code patterns
        pattern_suggestions = self.find_pattern_matches(text, coded_ranges, code_patterns, min_length, max_length)
        suggestions.extend(pattern_suggestions)
        
        # Strategy 3: Find descriptive passages (sensory details, setting descriptions)
        descriptive_suggestions = self.find_descriptive_segments(text, coded_ranges, min_length, max_length)
        suggestions.extend(descriptive_suggestions)
        
        # Strategy 4: Find character interactions
        interaction_suggestions = self.find_character_interactions(text, coded_ranges, min_length, max_length)
        suggestions.extend(interaction_suggestions)
        
        # Strategy 5: Find gaps between coded segments
        gap_suggestions = self.find_gaps_between_segments(text, coded_ranges, min_length, max_length)
        suggestions.extend(gap_suggestions)
        
        # Remove duplicates and sort by confidence
        unique_suggestions = self.deduplicate_suggestions(suggestions)
        unique_suggestions.sort(key=lambda x: x.get('confidence', 0.5), reverse=True)
        
        return unique_suggestions

    def get_code_patterns(self, codebook):
        """Get keywords and patterns associated with each code."""
        patterns = {}
        
        # Define patterns for key codes
        code_keywords = {
            'BELLONA_CITY': ['Bellona', 'city', 'urban', 'metropolis'],
            'URBAN_DECAY': ['ruin', 'decay', 'abandoned', 'derelict', 'crumbling', 'broken'],
            'FIRE_DESTRUCTION': ['fire', 'burn', 'flame', 'smoke', 'ash', 'destruction'],
            'SPATIAL_DISORIENTATION': ['lost', 'confused', 'direction', 'where', 'disorient', 'maze'],
            'ARCHITECTURE': ['building', 'structure', 'wall', 'door', 'window', 'room', 'house'],
            'SCORPIONS_GANG': ['Scorpion', 'gang', 'group'],
            'NOTEBOOK': ['notebook', 'journal', 'book', 'writing', 'page'],
            'WRITING_PROCESS': ['write', 'poem', 'poetry', 'verse', 'line'],
            'TEMPORAL_ANOMALY': ['time', 'moment', 'hour', 'day', 'night', 'morning', 'evening'],
            'REALITY_BREAK': ['strange', 'impossible', 'unreal', 'dream', 'hallucination'],
            'KID': ['Kid', 'he said', 'he thought', 'he felt'],
            'TAK': ['Tak', 'Taks'],
            'DENNY': ['Denny'],
            'SEXUAL_ENCOUNTER': ['touch', 'kiss', 'sex', 'body', 'skin', 'intimate'],
            'VIOLENCE': ['violence', 'fight', 'hit', 'strike', 'attack', 'hurt'],
            'SENSORY_DETAIL': ['saw', 'heard', 'felt', 'smell', 'taste', 'sound', 'light', 'dark'],
            'DIALOGUE': ['"', 'said', 'asked', 'replied', 'whispered'],
        }
        
        for code_name, keywords in code_keywords.items():
            try:
                code = Code.objects.get(codebook=codebook, code_name=code_name)
                patterns[code_name] = {
                    'code': code,
                    'keywords': keywords,
                    'pattern': re.compile('|'.join(keywords), re.IGNORECASE)
                }
            except Code.DoesNotExist:
                pass
        
        return patterns

    def find_dialogue_segments(self, text, coded_ranges, min_length, max_length):
        """Find dialogue segments (quoted text)."""
        suggestions = []
        # Match quoted text
        pattern = r'"[^"]{50,500}"'
        for match in re.finditer(pattern, text):
            start, end = match.span()
            if not self.is_overlapping(start, end, coded_ranges):
                suggestions.append({
                    'start': start,
                    'end': end,
                    'text': match.group(),
                    'codes': ['DIALOGUE'],
                    'reason': 'Dialogue segment',
                    'confidence': 0.8,
                })
        return suggestions

    def find_pattern_matches(self, text, coded_ranges, code_patterns, min_length, max_length):
        """Find segments matching code patterns."""
        suggestions = []
        
        # Look for segments with multiple keyword matches
        window_size = 300
        step = 100
        
        for start in range(0, len(text) - min_length, step):
            end = min(start + window_size, len(text))
            segment_text = text[start:end]
            
            if len(segment_text) < min_length:
                continue
            
            if self.is_overlapping(start, end, coded_ranges):
                continue
            
            # Count keyword matches
            matched_codes = []
            for code_name, pattern_data in code_patterns.items():
                matches = pattern_data['pattern'].findall(segment_text)
                if len(matches) >= 2:  # At least 2 keyword matches
                    matched_codes.append(code_name)
            
            if matched_codes:
                confidence = min(0.9, 0.5 + (len(matched_codes) * 0.1))
                suggestions.append({
                    'start': start,
                    'end': end,
                    'text': segment_text[:200],
                    'codes': matched_codes[:3],  # Top 3 codes
                    'reason': f'Matches patterns for: {", ".join(matched_codes[:3])}',
                    'confidence': confidence,
                })
        
        return suggestions

    def find_descriptive_segments(self, text, coded_ranges, min_length, max_length):
        """Find descriptive passages with sensory details."""
        suggestions = []
        
        # Look for long sentences with sensory words
        sensory_words = ['saw', 'heard', 'felt', 'smell', 'taste', 'sound', 'light', 'dark', 
                        'color', 'texture', 'warm', 'cold', 'bright', 'dim']
        sensory_pattern = re.compile('|'.join(sensory_words), re.IGNORECASE)
        
        # Split into sentences
        sentences = re.split(r'[.!?]\s+', text)
        current_pos = 0
        
        for sentence in sentences:
            if len(sentence) < min_length or len(sentence) > max_length:
                current_pos += len(sentence) + 2
                continue
            
            start = current_pos
            end = current_pos + len(sentence)
            current_pos = end + 2
            
            if self.is_overlapping(start, end, coded_ranges):
                continue
            
            sensory_matches = len(sensory_pattern.findall(sentence))
            if sensory_matches >= 2:
                suggestions.append({
                    'start': start,
                    'end': end,
                    'text': sentence[:200],
                    'codes': ['SENSORY_DETAIL', 'SETTING'],
                    'reason': f'Descriptive passage with {sensory_matches} sensory details',
                    'confidence': 0.6,
                })
        
        return suggestions

    def find_character_interactions(self, text, coded_ranges, min_length, max_length):
        """Find character interaction segments."""
        suggestions = []
        
        # Look for character names followed by actions
        character_names = ['Kid', 'Tak', 'Denny', 'Lopp', 'George']
        name_pattern = re.compile(r'\b(' + '|'.join(character_names) + r')\b', re.IGNORECASE)
        
        window_size = 200
        step = 100
        
        for start in range(0, len(text) - min_length, step):
            end = min(start + window_size, len(text))
            segment_text = text[start:end]
            
            if len(segment_text) < min_length:
                continue
            
            if self.is_overlapping(start, end, coded_ranges):
                continue
            
            names_found = name_pattern.findall(segment_text)
            if len(names_found) >= 1:
                # Determine which character
                char_code = None
                for name in names_found:
                    if name.upper() in ['KID']:
                        char_code = 'KID'
                    elif name.upper() in ['TAK', 'TAKS']:
                        char_code = 'TAK'
                    elif name.upper() == 'DENNY':
                        char_code = 'DENNY'
                
                if char_code:
                    suggestions.append({
                        'start': start,
                        'end': end,
                        'text': segment_text[:200],
                        'codes': [char_code, 'CHARACTER', 'DIALOGUE'] if '"' in segment_text else [char_code, 'CHARACTER'],
                        'reason': f'Character interaction: {char_code}',
                        'confidence': 0.7,
                    })
        
        return suggestions

    def find_gaps_between_segments(self, text, coded_ranges, min_length, max_length):
        """Find significant gaps between coded segments."""
        suggestions = []
        
        if not coded_ranges:
            return suggestions
        
        # Sort coded ranges
        sorted_ranges = sorted(coded_ranges)
        
        # Find gaps
        for i in range(len(sorted_ranges) - 1):
            gap_start = sorted_ranges[i][1]
            gap_end = sorted_ranges[i + 1][0]
            gap_size = gap_end - gap_start
            
            if gap_size >= min_length and gap_size <= max_length:
                gap_text = text[gap_start:gap_end]
                # Only suggest if gap has substantial content (not just whitespace)
                if len(gap_text.strip()) >= min_length:
                    suggestions.append({
                        'start': gap_start,
                        'end': gap_end,
                        'text': gap_text[:200],
                        'codes': ['SETTING', 'NARRATIVE_VOICE'],
                        'reason': f'Gap between coded segments ({gap_size} chars)',
                        'confidence': 0.5,
                    })
        
        return suggestions

    def is_overlapping(self, start, end, coded_ranges):
        """Check if a range overlaps with any coded range."""
        for coded_start, coded_end in coded_ranges:
            if not (end <= coded_start or start >= coded_end):
                return True
        return False

    def deduplicate_suggestions(self, suggestions):
        """Remove duplicate suggestions (same position)."""
        seen = set()
        unique = []
        for sug in suggestions:
            key = (sug['start'], sug['end'])
            if key not in seen:
                seen.add(key)
                unique.append(sug)
        return unique

    def auto_code_segments(self, analysis, suggestions, user, min_confidence=0.7):
        """Automatically code high-confidence segments."""
        created = 0
        
        for suggestion in suggestions:
            if suggestion.get('confidence', 0) < min_confidence:
                continue
            
            # Get code objects
            code_objects = []
            for code_name in suggestion['codes']:
                try:
                    code = Code.objects.get(codebook=analysis.codebook, code_name=code_name)
                    code_objects.append(code)
                except Code.DoesNotExist:
                    pass
            
            if not code_objects:
                continue
            
            # Create segment
            try:
                segment = CodedSegment.objects.create(
                    analysis=analysis,
                    start_position=suggestion['start'],
                    end_position=suggestion['end'],
                    text_excerpt=suggestion['text'][:500],  # Truncate if needed
                    location=f"Auto-coded: {suggestion['reason']}",
                    created_by=user,
                )
                segment.codes.set(code_objects)
                created += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Error creating segment: {e}'))
        
        return created

