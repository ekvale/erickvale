# PROMPT FOR DJANGO IMPLEMENTATION OF QUALITATIVE LITERARY ANALYSIS FRAMEWORK

## PROJECT OVERVIEW
Create a Django web application that implements a comprehensive qualitative literary analysis framework originally developed in Python. The system allows users to upload literary texts, apply systematic coding methodologies, and generate publication-quality analytical reports with statistical analysis, visualizations, and exports.

## CORE SYSTEM ARCHITECTURE

### 1. Data Models (literary_analysis.py)

**LiteraryText**
- Fields: title (str), author (str), text (str, full text content)
- Methods: get_segment(start, end) to extract text portions

**Code**
- Fields: 
  - code_name (str, unique identifier like "URBAN_DECAY")
  - code_type (str, one of: descriptive, process, emotion, values, structure)
  - definition (str, what this code captures)
  - examples (list of str, example applications)
  - parent_code (str or None, for hierarchical codes)

**Codebook**
- Fields: name (str), codes (dict of Code objects)
- Methods: add_code(), get_code(), list_codes_by_type()

**CodedSegment**
- Fields:
  - start_pos (int), end_pos (int) - character positions in text
  - codes (list of str, code names applied to this segment)
  - memo (str, analytical note about this segment)
  - location (str, descriptive location like "Page 45, Chapter 3")

**QualitativeAnalysis**
- Links: LiteraryText, Codebook
- Fields: coded_segments (list), memos (list of analytical memos)
- Methods:
  - code_segment(start, end, code_names, memo) - apply codes to text segment
  - get_code_frequency() - returns dict of code: count
  - export_analysis(json_path) - exports complete analysis to JSON

### 2. Advanced Analysis Modules (advanced_analysis.py)

**PatternDetector**
- find_repeated_phrases(min_length, min_frequency)
- find_symbolic_clusters()

**ThematicAnalyzer**
- create_theme(name, codes, description)
- get_theme_frequency(theme_name)
- track_theme_evolution()

**CharacterNetwork** (uses networkx)
- add_character(name)
- add_relationship(char1, char2, relationship_type)
- analyze_centrality()
- detect_communities()

**NarrativeArc**
- track_emotional_trajectory()
- identify_turning_points()

**LexicalAnalyzer**
- calculate_vocabulary_richness()
- get_word_frequency()
- calculate_ttr() - type-token ratio

### 3. Report Generation (reporting.py)

**HTMLReporter**
- Generates comprehensive HTML reports with:
  - Dark academic styling (custom CSS included)
  - Analysis overview
  - Complete codebook documentation
  - Code frequency tables with visualizations
  - Co-occurrence matrices
  - All coded segments with context
  - Analytical memos
  - JSON data export

**AdvancedReporter** (extends HTMLReporter)
- Adds: repeated pattern detection, lexical analysis, network visualizations

### 4. Specialized Analyzers (examples provided)

**Divine Comedy Analyzer** (divine_comedy_analyzer.py)
- Pre-built codebook with 70+ codes for Dante analysis:
  - Theological themes (sins, virtues, divine attributes)
  - Journey motifs (descent, ascent, transformation)
  - Literary devices (imagery, classical/biblical references)
- Automatic detection of structure (Inferno/Purgatorio/Paradiso)
- Famous passage identification

**Dhalgren Analyzer** (dhalgren_analyzer.py)
- Pre-built codebook with 65+ codes for experimental fiction:
  - Urban apocalypse (decay, Bellona, social collapse)
  - Identity & sexuality (fluidity, queer desire, polyamory)
  - Artistic creation (writing, poetry, metafiction)
  - Narrative structure (circularity, fragmentation)
- Character network setup (Kid, Lanya, Denny, etc.)
- Circular structure detection

## ENHANCED REPORTING FEATURES (generate_lightweight_report.py + add-ons)

### Statistical Analysis
- Chi-square tests on code co-occurrence
- Tests whether code pairs appear together more/less than expected by chance
- P-values with significance levels (*, **, ***)
- Interpretation: "codes co-occur MORE than expected" vs LESS

### Word Cloud & Lexical Analysis
- Extract all words from coded segments
- Filter stopwords
- Generate visual word cloud (size based on frequency)
- Top 30 words table with frequency bars
- Adapted for literary register (keeps words 4+ characters)

### Theme-Specific Excerpts
- For each of 7 major themes, show 3 representative full-text passages
- No truncation - complete context
- Display applied codes and location for each excerpt

### Segment Progression Timeline
- Visual timeline showing thematic flow through text
- Colored bars represent segments (color = dominant theme)
- Legend with 7 theme colors
- Table showing segment-by-segment progression
- Reveals clustering, narrative flow, structural patterns

### N-gram Analysis
- Tri-grams (3-word sequences) with frequency ≥2
- Bi-grams (2-word sequences) with frequency ≥3
- Filters out all-stopword sequences
- Categorizes tri-grams (character reference, urban decay, temporal, etc.)
- Visual display with size based on frequency

### Comparative Analysis (Beginning/Middle/End)
- Divides coded segments into thirds
- Compares code distribution across sections
- Identifies patterns: front-loaded, back-loaded, middle-focused, distributed
- Theme emphasis by section
- Shows narrative arc and thematic evolution

### Code Application Heatmap
- 10x10 grid showing code type density across text
- Each column = 10% of segments
- Each row = code type (descriptive, process, emotion, values, structure)
- Color intensity = concentration
- Reveals "hot spots" of intensive coding

### Sentiment/Affective Analysis
- Lexicon-based approach adapted for literary texts
- Positive words (love, joy, hope, etc.)
- Negative words (fear, pain, death, etc.)
- Intensity words (scream, explode, shatter)
- Visual timeline of affective charge
- Table of most emotionally intense segments
- Average sentiment scores

### Code Hierarchy Tree
- Visual tree structure organized by code type
- Shows parent-child relationships (indented subcodes)
- Usage bars for each code (width = frequency)
- Type totals and color coding
- Monospace font for tree structure

## DJANGO IMPLEMENTATION REQUIREMENTS

### Models (Django ORM)

```python
class LiteraryWork(models.Model):
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=200)
    text_file = models.FileField(upload_to='literary_texts/')
    uploaded_by = models.ForeignKey(User, on_delete=CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
class CodebookTemplate(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    is_public = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=CASCADE)
    # Specialized templates: "Divine Comedy", "Dhalgren", "Custom"
    
class Code(models.Model):
    codebook = models.ForeignKey(CodebookTemplate, on_delete=CASCADE)
    code_name = models.CharField(max_length=100)
    code_type = models.CharField(max_length=20, choices=[...])
    definition = models.TextField()
    parent_code = models.ForeignKey('self', null=True, blank=True)
    
class Analysis(models.Model):
    literary_work = models.ForeignKey(LiteraryWork, on_delete=CASCADE)
    codebook = models.ForeignKey(CodebookTemplate, on_delete=CASCADE)
    analyst = models.ForeignKey(User, on_delete=CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    json_data = models.JSONField()  # Stores complete analysis
    report_html = models.TextField(blank=True)  # Cached report
    
class CodedSegment(models.Model):
    analysis = models.ForeignKey(Analysis, on_delete=CASCADE)
    start_position = models.IntegerField()
    end_position = models.IntegerField()
    text_excerpt = models.TextField()
    location = models.CharField(max_length=200)
    memo = models.TextField(blank=True)
    codes = models.ManyToManyField(Code)
```

### Views Required

**1. Upload & Initialize**
- Upload literary text (txt file)
- Choose codebook template (Dhalgren, Divine Comedy, or Custom)
- If custom, create/edit codes

**2. Coding Interface**
- Display text with paragraph numbers or character positions
- Text selection tool to mark segments
- Multi-select dropdown to apply codes
- Memo field for analytical notes
- Save coded segment
- Show list of existing coded segments with edit/delete

**3. Analysis Dashboard**
- View code frequency distribution
- See co-occurrence matrix
- Filter segments by code
- Search within coded segments

**4. Report Generation**
- Button to generate comprehensive report
- Progress indicator (shows which sections are generating)
- Options to include/exclude sections:
  - [ ] Statistical analysis (chi-square)
  - [ ] Word cloud
  - [ ] Theme excerpts
  - [ ] Progression timeline
  - [ ] N-grams
  - [ ] Comparative analysis
  - [ ] Heatmap
  - [ ] Sentiment analysis
  - [ ] Hierarchy tree
- Download HTML report
- Download JSON data export

### Key Features

**Real-time Coding**
- AJAX-based segment coding without page reload
- Highlight coded segments in text (color by code type)
- Click coded segment to view/edit codes and memo

**Collaborative Features**
- Share codebook templates
- Multiple analysts can code same text (track who coded what)
- Compare inter-coder reliability

**Export Options**
- HTML report (self-contained, styled)
- JSON (structured data for further analysis)
- CSV (code frequencies, co-occurrence matrix)
- LaTeX (for academic papers)

**Performance Optimization**
- Generate report asynchronously using Celery
- Cache generated reports
- Only regenerate when analysis changes
- Lazy-load large text files

## TECHNICAL SPECIFICATIONS

### Dependencies
```
Django >= 4.2
networkx >= 2.8  # For character network analysis
scipy >= 1.10    # For chi-square statistical tests
numpy >= 1.24    # For statistical computations
```

### Report Generation Timing Targets
- Statistical analysis: ~1.4 seconds (chi-square on 20 code pairs)
- Word analysis: ~0.002 seconds
- All other sections: < 0.01 seconds each
- Total report generation: 1.4-2 seconds for 54 segments
- Final report size: ~250KB HTML

### File Storage
- Use Django's FileField for uploaded texts
- Store generated reports in media/reports/
- Store JSON exports in media/exports/
- Cache reports to avoid regeneration

### Security
- User authentication required
- Users can only access their own analyses
- Public codebook templates can be shared
- Sanitize uploaded text files (plain text only)
- Rate limit report generation (computationally expensive)

## USER WORKFLOW EXAMPLE

1. User uploads "Dhalgren" text file (1.7MB, 1.8M characters)
2. Selects "Dhalgren Specialized Analyzer" codebook template
3. System loads codebook with 65+ pre-configured codes
4. User begins coding:
   - Selects text: "The city was burning..."
   - Applies codes: URBAN_DECAY, FIRE_DESTRUCTION, BELLONA_CITY
   - Adds memo: "Opening imagery establishes apocalyptic setting"
   - Saves segment
5. User codes 54 segments over multiple sessions
6. User clicks "Generate Comprehensive Report"
7. System generates report with all features (1.4 seconds)
8. User downloads 253KB HTML report with:
   - Statistical significance tests
   - Word cloud visualization
   - Theme-specific excerpts
   - Progression timeline
   - N-gram analysis
   - Comparative analysis
   - Code heatmap
   - Sentiment analysis
   - Hierarchy tree
   - All 54 coded segments with full text
9. User exports JSON for further computational analysis

## SPECIAL CONSIDERATIONS

### Handling Large Texts
- Dhalgren example: 1.7M characters
- Don't load entire text into memory for display
- Paginate or show excerpts with context
- Store full text in file, reference positions

### Report Customization
- Let users toggle report sections on/off
- Some users may not want sentiment analysis
- Research papers may need different sections than teaching

### Codebook Flexibility
- Support custom code creation
- Allow importing/exporting codebooks as JSON
- Pre-built templates for common use cases:
  - Experimental fiction (Dhalgren)
  - Epic poetry (Divine Comedy)
  - General narrative fiction
  - Qualitative research interview coding

### Citation & Academic Use
- Reports should be citation-ready
- Include methodology notes
- Export to formats compatible with reference managers
- Generate suggested citations

## OUTPUT REQUIREMENTS

The Django app should provide:
1. Clean, academic-looking UI (not flashy, professional)
2. Comprehensive HTML reports with embedded CSS (self-contained)
3. JSON exports for computational analysis
4. User authentication and data privacy
5. Codebook template library
6. Fast report generation (< 2 seconds for typical analysis)
7. Mobile-responsive for text reading/coding on tablets

## EXAMPLE REPORT SECTIONS (IN ORDER)

1. Executive Summary (overview, statistics)
2. Statistical Analysis (chi-square tests with p-values)
3. Word Cloud & Lexical Analysis
4. Thematic Analysis (7 themes with detailed descriptions)
5. Complete Codebook Documentation
6. Code Frequency Analysis
7. Co-occurrence Network
8. Theme-Specific Text Excerpts
9. Segment Progression Timeline
10. N-gram Analysis (tri-grams and bi-grams)
11. Comparative Analysis (beginning/middle/end)
12. Code Application Heatmap
13. Sentiment/Affective Analysis
14. Code Hierarchy Tree
15. Complete Coded Segment Catalog (all segments)
16. Analytical Memos
17. Technical Documentation

Each section is self-contained with explanatory text, visualizations, and interpretive guidance.

## SUCCESS METRICS

- Report generation completes in < 2 seconds
- Users can code 50+ segments without performance degradation
- Reports are 200-300KB (comprehensive but not bloated)
- Codebook templates reduce setup time by 90%
- Export formats compatible with R, Python, SPSS for further analysis

This system brings rigorous qualitative research methodologies to digital humanities and literary analysis.
