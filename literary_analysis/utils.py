"""
Utilities for text processing and typo detection.
"""
import re
from collections import Counter


def detect_common_typos(text):
    """
    Detect common typos and OCR errors in text.
    Returns a list of potential typos with context.
    """
    typos = []
    
    # Common OCR/typo patterns
    patterns = [
        # Number 1 instead of letter I
        (r'\b1\s+([a-z]+)', r'I \1', 'Number "1" used instead of letter "I"'),
        (r'\b([a-z]+)\s+1\s+([a-z]+)', r'\1 I \2', 'Number "1" used instead of letter "I"'),
        
        # Common OCR errors
        (r'\baccuses\b', 'accusers', '"accuses" should be "accusers"?'),
        (r'\bbaJe\b', 'bad', '"baJe" should be "bad"?'),
        (r'\baU\b', 'all', '"aU" should be "all"?'),
        (r'\bten\b', 'tell', '"ten" should be "tell"? (context dependent)'),
        
        # Common character substitutions
        (r'fln\b', 'in', '"fln" should be "in"?'),
        (r'aud\b', 'and', '"aud" should be "and"?'),
    ]
    
    lines = text.split('\n')
    for line_num, line in enumerate(lines, 1):
        for pattern, replacement, description in patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                typos.append({
                    'line': line_num,
                    'position': match.start(),
                    'original': match.group(),
                    'suggestion': replacement,
                    'context': line[max(0, match.start()-50):match.end()+50],
                    'description': description
                })
    
    return typos


def find_suspicious_words(text, min_length=3):
    """
    Find words that might be typos by looking for:
    - Words with unusual character combinations
    - Words that appear only once (potential OCR errors)
    - Words with numbers mixed in
    """
    # Extract all words
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    word_freq = Counter(words)
    
    suspicious = []
    
    # Words that appear only once (might be typos)
    for word, count in word_freq.items():
        if count == 1 and len(word) >= min_length:
            # Check if it looks like a typo
            if has_unusual_pattern(word):
                suspicious.append({
                    'word': word,
                    'frequency': count,
                    'reason': 'Appears only once, unusual pattern'
                })
    
    return suspicious


def has_unusual_pattern(word):
    """Check if a word has unusual character patterns that might indicate a typo."""
    # Words with too many consonants in a row
    if re.search(r'[bcdfghjklmnpqrstvwxyz]{4,}', word):
        return True
    # Words with too many vowels in a row
    if re.search(r'[aeiou]{4,}', word):
        return True
    return False


def apply_typo_fix(text, line_num, position, original, replacement):
    """Apply a single typo fix to the text."""
    lines = text.split('\n')
    if line_num <= len(lines):
        line = lines[line_num - 1]
        # Replace first occurrence at or after position
        new_line = line[:position] + line[position:].replace(original, replacement, 1)
        lines[line_num - 1] = new_line
    return '\n'.join(lines)

