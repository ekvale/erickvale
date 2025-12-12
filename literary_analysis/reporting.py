"""
Comprehensive report generation for literary analysis.
Implements all 17 sections from the prompt.
"""
import json
import re
from collections import Counter, defaultdict
from itertools import combinations
from scipy.stats import chi2_contingency
import numpy as np
try:
    import networkx as nx
except ImportError:
    nx = None


class ReportGenerator:
    """Generates comprehensive HTML reports for literary analysis."""
    
    def __init__(self, analysis):
        self.analysis = analysis
        self.work = analysis.literary_work
        self.codebook = analysis.codebook
        self.segments = list(analysis.coded_segments.all().order_by('start_position'))
        self.codes = {code.code_name: code for code in self.codebook.codes.all()}
        
        # Load full text
        try:
            with self.work.text_file.open('r', encoding='utf-8') as f:
                self.full_text = f.read()
        except Exception:
            self.full_text = ""
    
    def generate_report(self, include_sections=None):
        """Generate complete HTML report."""
        if include_sections is None:
            include_sections = {
                'statistical': True,
                'word_cloud': True,
                'theme_excerpts': True,
                'progression': True,
                'ngrams': True,
                'comparative': True,
                'heatmap': True,
                'sentiment': True,
                'hierarchy': True,
            }
        
        html = self._get_html_header()
        html += self._section_executive_summary()
        
        if include_sections.get('statistical'):
            html += self._section_statistical_analysis()
        
        if include_sections.get('word_cloud'):
            html += self._section_word_cloud()
        
        html += self._section_thematic_analysis()
        html += self._section_codebook_documentation()
        html += self._section_code_frequency()
        html += self._section_co_occurrence()
        
        if include_sections.get('theme_excerpts'):
            html += self._section_theme_excerpts()
        
        if include_sections.get('progression'):
            html += self._section_progression_timeline()
        
        if include_sections.get('ngrams'):
            html += self._section_ngram_analysis()
        
        if include_sections.get('comparative'):
            html += self._section_comparative_analysis()
        
        if include_sections.get('heatmap'):
            html += self._section_heatmap()
        
        if include_sections.get('sentiment'):
            html += self._section_sentiment_analysis()
        
        if include_sections.get('hierarchy'):
            html += self._section_code_hierarchy()
        
        html += self._section_complete_segments()
        html += self._section_memos()
        html += self._section_technical_docs()
        html += self._get_html_footer()
        
        return html
    
    def _get_html_header(self):
        """HTML header with embedded CSS."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analysis Report: {self.work.title}</title>
    <style>
        {self._get_css()}
    </style>
</head>
<body>
    <div class="report-container">
        <header class="report-header">
            <h1>{self.work.title}</h1>
            <h2>by {self.work.author}</h2>
            <p class="subtitle">Qualitative Analysis Report</p>
            <p class="meta">Codebook: {self.codebook.name} | Segments: {len(self.segments)} | Generated: {self.analysis.updated_at.strftime('%B %d, %Y')}</p>
        </header>
"""
    
    def _get_css(self):
        """Dark academic styling CSS."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Georgia', 'Times New Roman', serif;
            background: #1a1a1a;
            color: #e0e0e0;
            line-height: 1.8;
            padding: 40px 20px;
        }
        .report-container {
            max-width: 1000px;
            margin: 0 auto;
            background: #0a0a0a;
            padding: 60px;
            border: 1px solid #2a2a2a;
        }
        .report-header {
            text-align: center;
            margin-bottom: 60px;
            padding-bottom: 40px;
            border-bottom: 2px solid #2a2a2a;
        }
        .report-header h1 {
            font-size: 42px;
            font-weight: 400;
            margin-bottom: 10px;
            color: #fff;
        }
        .report-header h2 {
            font-size: 24px;
            font-weight: 300;
            color: #ccc;
            margin-bottom: 20px;
        }
        .subtitle {
            font-size: 18px;
            color: #888;
            margin-bottom: 10px;
        }
        .meta {
            font-size: 14px;
            color: #666;
        }
        .section {
            margin-bottom: 60px;
            page-break-inside: avoid;
        }
        .section h2 {
            font-size: 32px;
            font-weight: 400;
            margin-bottom: 30px;
            color: #fff;
            border-bottom: 1px solid #2a2a2a;
            padding-bottom: 10px;
        }
        .section h3 {
            font-size: 24px;
            font-weight: 400;
            margin-top: 30px;
            margin-bottom: 20px;
            color: #fff;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #2a2a2a;
        }
        th {
            background: #1a1a1a;
            color: #fff;
            font-weight: 500;
        }
        .code-badge {
            display: inline-block;
            padding: 4px 8px;
            background: #2a2a2a;
            border: 1px solid #3a3a3a;
            border-radius: 4px;
            font-size: 12px;
            margin-right: 8px;
            margin-bottom: 8px;
        }
        .segment-box {
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }
        .segment-text {
            font-style: italic;
            color: #ccc;
            margin-bottom: 10px;
            line-height: 1.8;
        }
        .segment-meta {
            font-size: 14px;
            color: #888;
            margin-top: 10px;
        }
        .stat-significant {
            color: #4a9;
        }
        .stat-moderate {
            color: #9a4;
        }
        .stat-weak {
            color: #aa4;
        }
        .frequency-bar {
            height: 20px;
            background: #417690;
            border-radius: 2px;
            display: inline-block;
        }
        .excerpt {
            background: #1a1a1a;
            border-left: 4px solid #417690;
            padding: 20px;
            margin: 20px 0;
        }
        .timeline-bar {
            height: 30px;
            background: #417690;
            margin: 5px 0;
            border-radius: 2px;
        }
        .heatmap-cell {
            width: 30px;
            height: 30px;
            display: inline-block;
            margin: 2px;
            border: 1px solid #2a2a2a;
        }
        .hierarchy-tree {
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.6;
        }
        .tree-item {
            margin: 5px 0;
        }
        .tree-indent {
            display: inline-block;
            width: 20px;
        }
        """
    
    def _section_executive_summary(self):
        """Section 1: Executive Summary."""
        code_freq = self._get_code_frequency()
        total_codes = sum(code_freq.values())
        unique_codes = len(code_freq)
        
        html = f"""
        <section class="section">
            <h2>Executive Summary</h2>
            <p>This report presents a comprehensive qualitative analysis of <em>{self.work.title}</em> by {self.work.author}, 
            using the {self.codebook.name} codebook. The analysis includes {len(self.segments)} coded segments 
            representing {total_codes} code applications across {unique_codes} distinct codes.</p>
            
            <h3>Key Statistics</h3>
            <ul>
                <li><strong>Text Length:</strong> {len(self.full_text):,} characters</li>
                <li><strong>Coded Segments:</strong> {len(self.segments)}</li>
                <li><strong>Unique Codes Applied:</strong> {unique_codes}</li>
                <li><strong>Total Code Applications:</strong> {total_codes}</li>
                <li><strong>Average Codes per Segment:</strong> {total_codes / len(self.segments) if self.segments else 0:.2f}</li>
            </ul>
        </section>
        """
        return html
    
    def _section_statistical_analysis(self):
        """Section 2: Statistical Analysis (chi-square tests)."""
        html = """
        <section class="section">
            <h2>Statistical Analysis</h2>
            <p>Chi-square tests examine whether code pairs co-occur more or less frequently than expected by chance.</p>
        """
        
        # Get code pairs
        code_pairs = self._get_code_pairs()
        
        if code_pairs:
            html += """
            <table>
                <thead>
                    <tr>
                        <th>Code Pair</th>
                        <th>Observed</th>
                        <th>Expected</th>
                        <th>Chi-square</th>
                        <th>P-value</th>
                        <th>Significance</th>
                        <th>Interpretation</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            # Sort by chi-square value (most significant first)
            sorted_pairs = sorted(code_pairs.items(), key=lambda x: x[1]['chi2'], reverse=True)[:20]
            
            for (code1, code2), stats in sorted_pairs:
                p_value = stats['p_value']
                observed = stats['observed']
                expected = stats['expected']
                
                # Significance levels
                if p_value < 0.001:
                    sig = "***"
                    sig_class = "stat-significant"
                elif p_value < 0.01:
                    sig = "**"
                    sig_class = "stat-significant"
                elif p_value < 0.05:
                    sig = "*"
                    sig_class = "stat-moderate"
                else:
                    sig = ""
                    sig_class = "stat-weak"
                
                interpretation = "MORE" if observed > expected else "LESS"
                
                html += f"""
                    <tr>
                        <td>{code1} × {code2}</td>
                        <td>{observed}</td>
                        <td>{expected:.2f}</td>
                        <td>{stats['chi2']:.4f}</td>
                        <td>{p_value:.4f}</td>
                        <td class="{sig_class}">{sig}</td>
                        <td>Co-occur {interpretation} than expected</td>
                    </tr>
                """
            
            html += """
                </tbody>
            </table>
            <p><small>* p &lt; 0.05, ** p &lt; 0.01, *** p &lt; 0.001</small></p>
            """
        else:
            html += "<p>Insufficient data for statistical analysis.</p>"
        
        html += "</section>"
        return html
    
    def _section_word_cloud(self):
        """Section 3: Word Cloud & Lexical Analysis."""
        words = self._extract_words_from_segments()
        word_freq = Counter(words)
        top_words = word_freq.most_common(30)
        
        html = """
        <section class="section">
            <h2>Word Cloud & Lexical Analysis</h2>
            <p>Analysis of word frequency in coded segments (excluding stopwords, minimum 4 characters).</p>
            
            <h3>Top 30 Words</h3>
            <table>
                <thead>
                    <tr>
                        <th>Word</th>
                        <th>Frequency</th>
                        <th>Visualization</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        max_freq = top_words[0][1] if top_words else 1
        
        for word, freq in top_words:
            bar_width = (freq / max_freq) * 100
            html += f"""
                    <tr>
                        <td>{word}</td>
                        <td>{freq}</td>
                        <td><div class="frequency-bar" style="width: {bar_width}%;"></div></td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </section>
        """
        return html
    
    def _section_thematic_analysis(self):
        """Section 4: Thematic Analysis."""
        # Group codes by type
        themes = defaultdict(list)
        for code_name, code in self.codes.items():
            themes[code.code_type].append(code_name)
        
        html = """
        <section class="section">
            <h2>Thematic Analysis</h2>
            <p>Codes organized by thematic categories.</p>
        """
        
        for theme_type, code_list in themes.items():
            html += f"""
            <h3>{theme_type.title()}</h3>
            <ul>
            """
            for code_name in code_list:
                code = self.codes.get(code_name)
                if code:
                    html += f'<li><strong>{code_name}:</strong> {code.definition}</li>'
            html += "</ul>"
        
        html += "</section>"
        return html
    
    def _section_codebook_documentation(self):
        """Section 5: Complete Codebook Documentation."""
        html = """
        <section class="section">
            <h2>Complete Codebook Documentation</h2>
        """
        
        for code_type in ['descriptive', 'process', 'emotion', 'values', 'structure']:
            codes_of_type = [c for c in self.codebook.codes.all() if c.code_type == code_type]
            if codes_of_type:
                html += f"""
                <h3>{code_type.title()} Codes</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Code Name</th>
                            <th>Definition</th>
                            <th>Examples</th>
                        </tr>
                    </thead>
                    <tbody>
                """
                for code in codes_of_type:
                    examples = ', '.join(code.examples) if code.examples else 'None provided'
                    html += f"""
                        <tr>
                            <td><strong>{code.code_name}</strong></td>
                            <td>{code.definition}</td>
                            <td>{examples}</td>
                        </tr>
                    """
                html += """
                    </tbody>
                </table>
                """
        
        html += "</section>"
        return html
    
    def _section_code_frequency(self):
        """Section 6: Code Frequency Analysis."""
        code_freq = self._get_code_frequency()
        sorted_codes = sorted(code_freq.items(), key=lambda x: x[1], reverse=True)
        max_freq = sorted_codes[0][1] if sorted_codes else 1
        
        html = """
        <section class="section">
            <h2>Code Frequency Analysis</h2>
            <table>
                <thead>
                    <tr>
                        <th>Code</th>
                        <th>Frequency</th>
                        <th>Percentage</th>
                        <th>Visualization</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        total = sum(code_freq.values())
        
        for code_name, freq in sorted_codes:
            percentage = (freq / total * 100) if total > 0 else 0
            bar_width = (freq / max_freq) * 100
            html += f"""
                    <tr>
                        <td>{code_name}</td>
                        <td>{freq}</td>
                        <td>{percentage:.1f}%</td>
                        <td><div class="frequency-bar" style="width: {bar_width}%;"></div></td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </section>
        """
        return html
    
    def _section_co_occurrence(self):
        """Section 7: Co-occurrence Network."""
        html = """
        <section class="section">
            <h2>Co-occurrence Network</h2>
            <p>Codes that frequently appear together in the same segments.</p>
        """
        
        co_occurrence = self._get_co_occurrence_matrix()
        
        if co_occurrence:
            html += """
            <table>
                <thead>
                    <tr>
                        <th>Code 1</th>
                        <th>Code 2</th>
                        <th>Co-occurrences</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            sorted_pairs = sorted(co_occurrence.items(), key=lambda x: x[1], reverse=True)[:30]
            
            for (code1, code2), count in sorted_pairs:
                html += f"""
                    <tr>
                        <td>{code1}</td>
                        <td>{code2}</td>
                        <td>{count}</td>
                    </tr>
                """
            
            html += """
                </tbody>
            </table>
            """
        else:
            html += "<p>No significant co-occurrences found.</p>"
        
        html += "</section>"
        return html
    
    def _section_theme_excerpts(self):
        """Section 8: Theme-Specific Text Excerpts."""
        # Group segments by dominant code type
        theme_segments = defaultdict(list)
        for segment in self.segments:
            for code in segment.codes.all():
                theme_segments[code.code_type].append((segment, code.code_name))
        
        html = """
        <section class="section">
            <h2>Theme-Specific Text Excerpts</h2>
            <p>Representative full-text passages for each major theme.</p>
        """
        
        for theme_type, seg_list in list(theme_segments.items())[:7]:  # Top 7 themes
            html += f"""
            <h3>{theme_type.title()}</h3>
            """
            
            # Get 3 representative segments
            for segment, code_name in seg_list[:3]:
                html += f"""
                <div class="excerpt">
                    <div class="segment-text">"{segment.text_excerpt}"</div>
                    <div class="segment-meta">
                        <strong>Codes:</strong> {code_name}
                        {f'<br><strong>Location:</strong> {segment.location}' if segment.location else ''}
                    </div>
                </div>
                """
        
        html += "</section>"
        return html
    
    def _section_progression_timeline(self):
        """Section 9: Segment Progression Timeline."""
        html = """
        <section class="section">
            <h2>Segment Progression Timeline</h2>
            <p>Visual timeline showing thematic flow through the text.</p>
        """
        
        if self.segments:
            segment_size = 100 / len(self.segments)
            
            html += '<div style="margin: 20px 0;">'
            for i, segment in enumerate(self.segments):
                # Get dominant code type for color
                code_types = [code.code_type for code in segment.codes.all()]
                dominant_type = max(set(code_types), key=code_types.count) if code_types else 'descriptive'
                
                # Color mapping
                colors = {
                    'descriptive': '#417690',
                    'process': '#9a4',
                    'emotion': '#a94',
                    'values': '#4a9',
                    'structure': '#94a',
                }
                color = colors.get(dominant_type, '#666')
                
                html += f"""
                <div class="timeline-bar" style="width: {segment_size}%; background: {color};" 
                     title="Segment {i+1}: {', '.join([c.code_name for c in segment.codes.all()])}">
                </div>
                """
            html += '</div>'
            
            html += """
            <table>
                <thead>
                    <tr>
                        <th>Segment</th>
                        <th>Position</th>
                        <th>Codes</th>
                        <th>Dominant Theme</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for i, segment in enumerate(self.segments):
                code_types = [code.code_type for code in segment.codes.all()]
                dominant_type = max(set(code_types), key=code_types.count) if code_types else 'N/A'
                code_names = ', '.join([c.code_name for c in segment.codes.all()])
                
                html += f"""
                    <tr>
                        <td>{i+1}</td>
                        <td>{segment.start_position}-{segment.end_position}</td>
                        <td>{code_names}</td>
                        <td>{dominant_type}</td>
                    </tr>
                """
            
            html += """
                </tbody>
            </table>
            """
        
        html += "</section>"
        return html
    
    def _section_ngram_analysis(self):
        """Section 10: N-gram Analysis."""
        html = """
        <section class="section">
            <h2>N-gram Analysis</h2>
            <p>Frequent word sequences in coded segments.</p>
        """
        
        # Extract trigrams and bigrams
        trigrams = self._extract_ngrams(3, min_freq=2)
        bigrams = self._extract_ngrams(2, min_freq=3)
        
        if trigrams:
            html += """
            <h3>Tri-grams (3-word sequences, frequency ≥ 2)</h3>
            <ul>
            """
            for ngram, freq in trigrams[:20]:
                html += f'<li><strong>{" ".join(ngram)}</strong> ({freq} occurrences)</li>'
            html += "</ul>"
        
        if bigrams:
            html += """
            <h3>Bi-grams (2-word sequences, frequency ≥ 3)</h3>
            <ul>
            """
            for ngram, freq in bigrams[:20]:
                html += f'<li><strong>{" ".join(ngram)}</strong> ({freq} occurrences)</li>'
            html += "</ul>"
        
        html += "</section>"
        return html
    
    def _section_comparative_analysis(self):
        """Section 11: Comparative Analysis (Beginning/Middle/End)."""
        if not self.segments:
            return "<section class='section'><h2>Comparative Analysis</h2><p>No segments to analyze.</p></section>"
        
        # Divide into thirds
        third = len(self.segments) // 3
        beginning = self.segments[:third]
        middle = self.segments[third:2*third]
        end = self.segments[2*third:]
        
        def get_code_freq(segments):
            freq = Counter()
            for seg in segments:
                for code in seg.codes.all():
                    freq[code.code_name] += 1
            return freq
        
        beg_freq = get_code_freq(beginning)
        mid_freq = get_code_freq(middle)
        end_freq = get_code_freq(end)
        
        all_codes = set(beg_freq.keys()) | set(mid_freq.keys()) | set(end_freq.keys())
        
        html = """
        <section class="section">
            <h2>Comparative Analysis: Beginning / Middle / End</h2>
            <p>Code distribution across three sections of the text.</p>
            <table>
                <thead>
                    <tr>
                        <th>Code</th>
                        <th>Beginning</th>
                        <th>Middle</th>
                        <th>End</th>
                        <th>Pattern</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for code_name in sorted(all_codes):
            b = beg_freq.get(code_name, 0)
            m = mid_freq.get(code_name, 0)
            e = end_freq.get(code_name, 0)
            
            # Determine pattern
            if b > m and b > e:
                pattern = "Front-loaded"
            elif e > b and e > m:
                pattern = "Back-loaded"
            elif m > b and m > e:
                pattern = "Middle-focused"
            else:
                pattern = "Distributed"
            
            html += f"""
                    <tr>
                        <td>{code_name}</td>
                        <td>{b}</td>
                        <td>{m}</td>
                        <td>{e}</td>
                        <td>{pattern}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </section>
        """
        return html
    
    def _section_heatmap(self):
        """Section 12: Code Application Heatmap."""
        html = """
        <section class="section">
            <h2>Code Application Heatmap</h2>
            <p>10x10 grid showing code type density across text segments.</p>
        """
        
        if self.segments:
            # Divide segments into 10 groups
            segment_groups = [self.segments[i::10] for i in range(10)]
            code_types = ['descriptive', 'process', 'emotion', 'values', 'structure']
            
            html += """
            <table>
                <thead>
                    <tr>
                        <th>Code Type</th>
                        <th colspan="10">Text Sections (10% each)</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for code_type in code_types:
                html += f"<tr><td>{code_type}</td>"
                for group in segment_groups:
                    count = sum(1 for seg in group for code in seg.codes.all() if code.code_type == code_type)
                    intensity = min(255, count * 50)  # Scale intensity
                    html += f'<td class="heatmap-cell" style="background: rgb({intensity}, {intensity//2}, {intensity//3});" title="{count}"></td>'
                html += "</tr>"
            
            html += """
                </tbody>
            </table>
            """
        
        html += "</section>"
        return html
    
    def _section_sentiment_analysis(self):
        """Section 13: Sentiment/Affective Analysis."""
        # Simple lexicon-based approach
        positive_words = {'love', 'joy', 'hope', 'beautiful', 'wonderful', 'happy', 'peace', 'light'}
        negative_words = {'fear', 'pain', 'death', 'dark', 'sad', 'anger', 'hate', 'despair'}
        intensity_words = {'scream', 'explode', 'shatter', 'crush', 'devastate', 'overwhelm'}
        
        segment_sentiments = []
        for segment in self.segments:
            words = set(re.findall(r'\b\w+\b', segment.text_excerpt.lower()))
            pos = len(words & positive_words)
            neg = len(words & negative_words)
            intense = len(words & intensity_words)
            score = pos - neg + (intense * 0.5)
            segment_sentiments.append((segment, score))
        
        html = """
        <section class="section">
            <h2>Sentiment/Affective Analysis</h2>
            <p>Lexicon-based sentiment analysis of coded segments.</p>
        """
        
        if segment_sentiments:
            avg_sentiment = sum(s[1] for s in segment_sentiments) / len(segment_sentiments)
            html += f'<p><strong>Average Sentiment Score:</strong> {avg_sentiment:.2f}</p>'
            
            # Most intense segments
            sorted_segments = sorted(segment_sentiments, key=lambda x: abs(x[1]), reverse=True)[:10]
            
            html += """
            <h3>Most Emotionally Intense Segments</h3>
            <table>
                <thead>
                    <tr>
                        <th>Segment</th>
                        <th>Sentiment Score</th>
                        <th>Excerpt</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for segment, score in sorted_segments:
                html += f"""
                    <tr>
                        <td>{segment.start_position}-{segment.end_position}</td>
                        <td>{score:.2f}</td>
                        <td>{segment.text_excerpt[:100]}...</td>
                    </tr>
                """
            
            html += """
                </tbody>
            </table>
            """
        
        html += "</section>"
        return html
    
    def _section_code_hierarchy(self):
        """Section 14: Code Hierarchy Tree."""
        html = """
        <section class="section">
            <h2>Code Hierarchy Tree</h2>
            <div class="hierarchy-tree">
        """
        
        code_freq = self._get_code_frequency()
        
        # Group by type
        by_type = defaultdict(list)
        for code in self.codebook.codes.all():
            by_type[code.code_type].append(code)
        
        for code_type, codes_list in by_type.items():
            html += f'<div class="tree-item"><strong>{code_type.upper()}</strong></div>'
            for code in codes_list:
                freq = code_freq.get(code.code_name, 0)
                bar_width = min(200, freq * 10)
                indent = '<span class="tree-indent"></span>' if code.parent_code else ''
                html += f"""
                <div class="tree-item">
                    {indent}{code.code_name} 
                    <span style="display: inline-block; width: {bar_width}px; height: 12px; background: #417690; margin-left: 10px;"></span>
                    ({freq})
                </div>
                """
        
        html += """
            </div>
        </section>
        """
        return html
    
    def _section_complete_segments(self):
        """Section 15: Complete Coded Segment Catalog."""
        html = """
        <section class="section">
            <h2>Complete Coded Segment Catalog</h2>
            <p>All coded segments with full context.</p>
        """
        
        for i, segment in enumerate(self.segments, 1):
            code_names = ', '.join([c.code_name for c in segment.codes.all()])
            html += f"""
            <div class="segment-box">
                <div class="segment-text">"{segment.text_excerpt}"</div>
                <div class="segment-meta">
                    <strong>Segment {i}</strong> | 
                    Position: {segment.start_position}-{segment.end_position} | 
                    Codes: {code_names}
                    {f'<br><strong>Location:</strong> {segment.location}' if segment.location else ''}
                    {f'<br><strong>Memo:</strong> {segment.memo}' if segment.memo else ''}
                </div>
            </div>
            """
        
        html += "</section>"
        return html
    
    def _section_memos(self):
        """Section 16: Analytical Memos."""
        memos = self.analysis.memos.all()
        
        html = f"""
        <section class="section">
            <h2>Analytical Memos</h2>
        """
        
        if memos:
            for memo in memos:
                html += f"""
                <div class="segment-box">
                    <h3>{memo.title}</h3>
                    <p>{memo.content}</p>
                    <div class="segment-meta">Created: {memo.created_at.strftime('%B %d, %Y')}</div>
                </div>
                """
        else:
            html += "<p>No analytical memos recorded.</p>"
        
        html += "</section>"
        return html
    
    def _section_technical_docs(self):
        """Section 17: Technical Documentation."""
        html = f"""
        <section class="section">
            <h2>Technical Documentation</h2>
            <h3>Methodology</h3>
            <p>This analysis was conducted using systematic qualitative coding methodology. 
            Text segments were identified and coded using the {self.codebook.name} codebook, 
            which contains {self.codebook.codes.count()} distinct codes organized by type.</p>
            
            <h3>Data Export</h3>
            <p>The complete analysis data is available in JSON format for further computational analysis.</p>
            
            <h3>Report Generation</h3>
            <p>Report generated on {self.analysis.updated_at.strftime('%B %d, %Y at %I:%M %p')} 
            using the Literary Analysis Framework.</p>
        </section>
        """
        return html
    
    def _get_html_footer(self):
        """HTML footer."""
        return """
    </div>
</body>
</html>
        """
    
    # Helper methods
    
    def _get_code_frequency(self):
        """Calculate code frequency."""
        freq = Counter()
        for segment in self.segments:
            for code in segment.codes.all():
                freq[code.code_name] += 1
        return freq
    
    def _get_code_pairs(self):
        """Get code pairs with chi-square statistics (optimized)."""
        if not self.segments:
            return {}
        
        pairs = {}
        
        # Pre-compute code occurrences for all segments (much faster)
        segment_codes = {}  # segment_id -> set of code names
        code_counts = Counter()  # code_name -> count
        
        for seg in self.segments:
            code_names = {c.code_name for c in seg.codes.all()}
            segment_codes[seg.id] = code_names
            for code_name in code_names:
                code_counts[code_name] += 1
        
        # Only process codes that actually appear
        active_codes = [code for code in self.codes.keys() if code_counts[code] > 0]
        
        # Limit to top 30 most frequent codes to avoid combinatorial explosion
        active_codes = sorted(active_codes, key=lambda x: code_counts[x], reverse=True)[:30]
        
        # Get all code pairs that co-occur
        for code1, code2 in combinations(active_codes, 2):
            # Count co-occurrences (fast set intersection)
            together = sum(1 for seg_id, codes in segment_codes.items() 
                          if code1 in codes and code2 in codes)
            
            if together > 0:
                code1_count = code_counts[code1]
                code2_count = code_counts[code2]
                
                # Expected frequency
                expected = (code1_count * code2_count) / len(self.segments) if self.segments else 0
                
                # Chi-square test (2x2 contingency table)
                observed = together
                if expected > 0 and len(self.segments) > 0:
                    # Create contingency table
                    a = together  # both
                    b = code1_count - together  # code1 but not code2
                    c = code2_count - together  # code2 but not code1
                    d = len(self.segments) - code1_count - code2_count + together  # neither
                    
                    if a + b > 0 and c + d > 0 and a + c > 0 and b + d > 0:
                        try:
                            contingency = np.array([[a, b], [c, d]])
                            chi2, p_value, dof, expected_table = chi2_contingency(contingency)
                        except:
                            chi2 = ((observed - expected) ** 2) / expected if expected > 0 else 0
                            p_value = 0.1
                    else:
                        chi2 = 0
                        p_value = 1.0
                else:
                    chi2 = 0
                    p_value = 1.0
                
                pairs[(code1, code2)] = {
                    'observed': observed,
                    'expected': expected,
                    'chi2': chi2,
                    'p_value': p_value
                }
        
        return pairs
    
    def _extract_words_from_segments(self):
        """Extract words from all coded segments."""
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'was', 'are', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        words = []
        for segment in self.segments:
            text_words = re.findall(r'\b\w+\b', segment.text_excerpt.lower())
            words.extend([w for w in text_words if len(w) >= 4 and w not in stopwords])
        
        return words
    
    def _get_co_occurrence_matrix(self):
        """Get co-occurrence counts for code pairs."""
        co_occur = Counter()
        for segment in self.segments:
            code_names = [c.code_name for c in segment.codes.all()]
            for code1, code2 in combinations(code_names, 2):
                co_occur[(code1, code2)] += 1
        return co_occur
    
    def _extract_ngrams(self, n, min_freq=2):
        """Extract n-grams from segments."""
        ngrams = Counter()
        for segment in self.segments:
            words = re.findall(r'\b\w+\b', segment.text_excerpt.lower())
            for i in range(len(words) - n + 1):
                ngram = tuple(words[i:i+n])
                ngrams[ngram] += 1
        
        # Filter by minimum frequency
        return [(ngram, freq) for ngram, freq in ngrams.items() if freq >= min_freq]

