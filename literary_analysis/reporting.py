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
            if self.work.text_file:
                with open(self.work.text_file.path, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                # Decode Unicode escape sequences if present
                if '\\u' in text or '\\U' in text:
                    import re
                    def replace_unicode(match):
                        code = match.group(1)
                        try:
                            if len(code) == 4:
                                return chr(int(code, 16))
                            elif len(code) == 8:
                                return chr(int(code, 16))
                        except (ValueError, OverflowError):
                            return match.group(0)
                        return match.group(0)
                    text = re.sub(r'\\u([0-9a-fA-F]{4})', replace_unicode, text)
                    text = re.sub(r'\\U([0-9a-fA-F]{8})', replace_unicode, text)
                    text = text.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r')
                    text = text.replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')
                
                self.full_text = text
            else:
                self.full_text = ""
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
        """HTML header with embedded CSS and Chart.js."""
        code_freq = self._get_code_frequency()
        sorted_codes = sorted(code_freq.items(), key=lambda x: x[1], reverse=True)[:20]  # Top 20 for charts
        
        # Prepare chart data
        chart_data = {
            'labels': [code[0] for code in sorted_codes],
            'frequencies': [code[1] for code in sorted_codes],
        }
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analysis Report: {self.work.title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
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
        
        <div class="controls-bar">
            <input type="text" id="search-input" placeholder="🔍 Search report..." class="search-box">
            <select id="section-filter" class="section-filter">
                <option value="">All Sections</option>
                <option value="executive">Executive Summary</option>
                <option value="statistical">Statistical Analysis</option>
                <option value="word">Word Cloud</option>
                <option value="thematic">Thematic Analysis</option>
                <option value="codebook">Codebook</option>
                <option value="frequency">Code Frequency</option>
                <option value="co-occurrence">Co-occurrence</option>
                <option value="segments">Coded Segments</option>
                <option value="memos">Memos</option>
            </select>
            <button onclick="scrollToTop()" class="btn-top">↑ Top</button>
        </div>
        
        <script>
            // Chart data
            const chartData = {json.dumps(chart_data)};
            
            // Enhanced search with highlighting
            let searchTimeout;
            document.getElementById('search-input').addEventListener('input', function(e) {{
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {{
                    const searchTerm = e.target.value.trim().toLowerCase();
                    const sectionFilter = document.getElementById('section-filter').value;
                    
                    // Remove previous highlights
                    document.querySelectorAll('.highlight').forEach(el => {{
                        const parent = el.parentNode;
                        parent.replaceChild(document.createTextNode(el.textContent), el);
                        parent.normalize();
                    }});
                    
                    if (searchTerm === '') {{
                        document.querySelectorAll('.section').forEach(s => {{
                            s.style.display = 'block';
                            s.classList.remove('hidden');
                        }});
                        return;
                    }}
                    
                    // Filter by section
                    document.querySelectorAll('.section').forEach(section => {{
                        const sectionId = section.id || '';
                        if (sectionFilter && !sectionId.includes(sectionFilter)) {{
                            section.style.display = 'none';
                            section.classList.add('hidden');
                            return;
                        }}
                        
                        const text = section.textContent.toLowerCase();
                        if (text.includes(searchTerm)) {{
                            section.style.display = 'block';
                            section.classList.remove('hidden');
                            
                            // Highlight matches
                            const walker = document.createTreeWalker(
                                section,
                                NodeFilter.SHOW_TEXT,
                                null,
                                false
                            );
                            
                            const textNodes = [];
                            let node;
                            while (node = walker.nextNode()) {{
                                if (node.textContent.toLowerCase().includes(searchTerm)) {{
                                    textNodes.push(node);
                                }}
                            }}
                            
                            textNodes.forEach(textNode => {{
                                const text = textNode.textContent;
                                const regex = new RegExp(`(${{searchTerm}})`, 'gi');
                                const highlighted = text.replace(regex, '<span class="highlight">$1</span>');
                                const wrapper = document.createElement('span');
                                wrapper.innerHTML = highlighted;
                                textNode.parentNode.replaceChild(wrapper, textNode);
                            }});
                        }} else {{
                            section.style.display = 'none';
                            section.classList.add('hidden');
                        }}
                    }});
                }}, 300);
            }});
            
            // Section filter
            document.getElementById('section-filter').addEventListener('change', function(e) {{
                const filter = e.target.value;
                document.querySelectorAll('.section').forEach(section => {{
                    const sectionId = section.id || '';
                    if (!filter || sectionId.includes(filter)) {{
                        section.style.display = 'block';
                        section.classList.remove('hidden');
                    }} else {{
                        section.style.display = 'none';
                        section.classList.add('hidden');
                    }}
                }});
            }});
            
            // Enhanced sortable tables with visual indicators
            function makeSortable(table) {{
                const headers = table.querySelectorAll('th');
                headers.forEach((header, index) => {{
                    header.classList.add('sortable');
                    header.style.cursor = 'pointer';
                    header.addEventListener('click', () => {{
                        sortTable(table, index, header);
                    }});
                }});
            }}
            
            function sortTable(table, columnIndex, header) {{
                const tbody = table.querySelector('tbody');
                const rows = Array.from(tbody.querySelectorAll('tr'));
                
                // Reset all headers
                table.querySelectorAll('th').forEach(th => {{
                    th.classList.remove('sort-asc', 'sort-desc');
                }});
                
                // Determine sort direction
                const currentSort = header.classList.contains('sort-asc') ? 'asc' : 
                                   header.classList.contains('sort-desc') ? 'desc' : 'none';
                const isAsc = currentSort !== 'asc';
                
                rows.sort((a, b) => {{
                    const aText = a.cells[columnIndex].textContent.trim();
                    const bText = b.cells[columnIndex].textContent.trim();
                    const aNum = parseFloat(aText.replace(/[^0-9.-]/g, ''));
                    const bNum = parseFloat(bText.replace(/[^0-9.-]/g, ''));
                    
                    if (!isNaN(aNum) && !isNaN(bNum)) {{
                        return isAsc ? aNum - bNum : bNum - aNum;
                    }}
                    return isAsc ? aText.localeCompare(bText) : bText.localeCompare(aText);
                }});
                
                rows.forEach(row => tbody.appendChild(row));
                
                // Update header class
                header.classList.remove('sort-asc', 'sort-desc');
                header.classList.add(isAsc ? 'sort-asc' : 'sort-desc');
            }}
            
            function scrollToTop() {{
                window.scrollTo({{ top: 0, behavior: 'smooth' }});
            }}
            
            // Initialize on load
            document.addEventListener('DOMContentLoaded', function() {{
                document.querySelectorAll('table').forEach(makeSortable);
                
                // Add IDs to sections for filtering
                document.querySelectorAll('.section').forEach((section, index) => {{
                    const h2 = section.querySelector('h2');
                    if (h2) {{
                        const id = h2.textContent.toLowerCase()
                            .replace(/[^a-z0-9]+/g, '-')
                            .replace(/^-|-$/g, '');
                        section.id = id;
                    }}
                }});
            }});
        </script>
"""
    
    def _get_css(self):
        """Enhanced colorful, modern styling CSS."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
            color: #e0e0e0;
            line-height: 1.8;
            padding: 20px;
        }
        .report-container {
            max-width: 1400px;
            margin: 0 auto;
            background: #0a0a0a;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.5);
        }
        .report-header {
            text-align: center;
            margin-bottom: 50px;
            padding: 40px;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 12px;
            border: 2px solid #2a4a6e;
            box-shadow: 0 4px 20px rgba(26, 26, 46, 0.5);
        }
        .report-header h1 {
            font-size: 48px;
            font-weight: 300;
            margin-bottom: 10px;
            color: #fff;
            text-shadow: 0 2px 10px rgba(255,255,255,0.1);
        }
        .report-header h2 {
            font-size: 28px;
            font-weight: 300;
            color: #a0c4ff;
            margin-bottom: 20px;
        }
        .subtitle {
            font-size: 20px;
            color: #888;
            margin-bottom: 10px;
        }
        .meta {
            font-size: 14px;
            color: #666;
            margin-top: 15px;
        }
        .controls-bar {
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(10, 10, 10, 0.95);
            backdrop-filter: blur(10px);
            padding: 15px 20px;
            margin: -20px -20px 30px -20px;
            border-bottom: 2px solid #2a2a2a;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }
        .search-box {
            flex: 1;
            min-width: 250px;
            padding: 12px 20px;
            background: #1a1a1a;
            border: 2px solid #2a2a2a;
            border-radius: 8px;
            color: #e0e0e0;
            font-size: 16px;
            transition: all 0.3s;
        }
        .search-box:focus {
            outline: none;
            border-color: #417690;
            box-shadow: 0 0 10px rgba(65, 118, 144, 0.3);
        }
        .section-filter {
            padding: 12px 20px;
            background: #1a1a1a;
            border: 2px solid #2a2a2a;
            border-radius: 8px;
            color: #e0e0e0;
            font-size: 14px;
            cursor: pointer;
        }
        .btn-top {
            padding: 12px 24px;
            background: linear-gradient(135deg, #417690 0%, #5a8ba5 100%);
            border: none;
            border-radius: 8px;
            color: #fff;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 10px rgba(65, 118, 144, 0.3);
        }
        .btn-top:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 15px rgba(65, 118, 144, 0.5);
        }
        .section {
            margin-bottom: 60px;
            padding: 40px;
            background: linear-gradient(135deg, #1a1a1a 0%, #0f0f0f 100%);
            border-radius: 12px;
            border: 2px solid #2a2a2a;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            page-break-inside: avoid;
            transition: all 0.3s;
        }
        .section:hover {
            border-color: #3a3a3a;
            box-shadow: 0 6px 30px rgba(0,0,0,0.4);
        }
        .section.hidden {
            display: none;
        }
        .section h2 {
            font-size: 36px;
            font-weight: 400;
            margin-bottom: 30px;
            color: #fff;
            padding-bottom: 15px;
            border-bottom: 3px solid;
            border-image: linear-gradient(90deg, #417690, #9a4, #4a9) 1;
        }
        .section h3 {
            font-size: 26px;
            font-weight: 400;
            margin-top: 30px;
            margin-bottom: 20px;
            color: #a0c4ff;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .stat-card {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 25px;
            border-radius: 10px;
            border: 2px solid #2a4a6e;
            text-align: center;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(26, 26, 46, 0.3);
        }
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(26, 26, 46, 0.5);
            border-color: #3a5a8e;
        }
        .stat-value {
            font-size: 42px;
            font-weight: 300;
            color: #a0c4ff;
            margin-bottom: 8px;
        }
        .stat-label {
            color: #888;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            background: #0a0a0a;
            border-radius: 8px;
            overflow: hidden;
        }
        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #2a2a2a;
        }
        th {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            font-weight: 500;
            cursor: pointer;
            user-select: none;
            position: relative;
            transition: background 0.3s;
        }
        th:hover {
            background: linear-gradient(135deg, #2a2a4e 0%, #26314e 100%);
        }
        th.sortable::after {
            content: ' ↕';
            opacity: 0.5;
            font-size: 12px;
        }
        th.sort-asc::after {
            content: ' ↑';
            opacity: 1;
            color: #4a9;
        }
        th.sort-desc::after {
            content: ' ↓';
            opacity: 1;
            color: #9a4;
        }
        tr:hover {
            background: #1a1a1a;
        }
        .code-badge {
            display: inline-block;
            padding: 6px 12px;
            background: linear-gradient(135deg, #2a4a6e 0%, #1a3a5e 100%);
            border: 1px solid #3a5a8e;
            border-radius: 6px;
            font-size: 12px;
            margin-right: 8px;
            margin-bottom: 8px;
            color: #a0c4ff;
            font-weight: 500;
        }
        .segment-box {
            background: linear-gradient(135deg, #1a1a1a 0%, #0f0f0f 100%);
            border-left: 5px solid #417690;
            padding: 25px;
            margin: 25px 0;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: all 0.3s;
        }
        .segment-box:hover {
            border-left-color: #5a8ba5;
            box-shadow: 0 6px 20px rgba(0,0,0,0.3);
        }
        .segment-text {
            font-style: italic;
            color: #ccc;
            margin-bottom: 15px;
            line-height: 1.8;
            font-size: 16px;
        }
        .segment-meta {
            font-size: 14px;
            color: #888;
            margin-top: 15px;
        }
        .stat-significant {
            color: #4a9;
            font-weight: 600;
        }
        .stat-moderate {
            color: #9a4;
            font-weight: 600;
        }
        .stat-weak {
            color: #aa4;
        }
        .frequency-bar {
            height: 24px;
            background: linear-gradient(90deg, #417690 0%, #5a8ba5 100%);
            border-radius: 4px;
            display: inline-block;
            min-width: 4px;
            box-shadow: 0 2px 8px rgba(65, 118, 144, 0.3);
        }
        .chart-container {
            background: #0a0a0a;
            padding: 30px;
            border-radius: 12px;
            margin: 30px 0;
            border: 2px solid #2a2a2a;
            position: relative;
            height: 400px;
        }
        .chart-wrapper {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
            margin: 30px 0;
        }
        .chart-card {
            background: #0a0a0a;
            padding: 25px;
            border-radius: 12px;
            border: 2px solid #2a2a2a;
            height: 350px;
        }
        .excerpt {
            background: linear-gradient(135deg, #1a1a1a 0%, #0f0f0f 100%);
            border-left: 5px solid #9a4;
            padding: 25px;
            margin: 25px 0;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .timeline-bar {
            height: 35px;
            background: linear-gradient(90deg, #417690 0%, #5a8ba5 100%);
            margin: 8px 0;
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(65, 118, 144, 0.3);
            transition: all 0.3s;
        }
        .timeline-bar:hover {
            transform: scaleX(1.02);
            box-shadow: 0 4px 12px rgba(65, 118, 144, 0.5);
        }
        .heatmap-cell {
            width: 35px;
            height: 35px;
            display: inline-block;
            margin: 3px;
            border: 2px solid #2a2a2a;
            border-radius: 4px;
            transition: all 0.2s;
        }
        .heatmap-cell:hover {
            transform: scale(1.2);
            z-index: 10;
            position: relative;
        }
        .hierarchy-tree {
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.8;
            background: #0a0a0a;
            padding: 25px;
            border-radius: 8px;
            border: 2px solid #2a2a2a;
        }
        .tree-item {
            margin: 8px 0;
            color: #ccc;
        }
        .tree-indent {
            display: inline-block;
            width: 25px;
        }
        .highlight {
            background: rgba(154, 164, 0, 0.4);
            padding: 2px 4px;
            border-radius: 3px;
            font-weight: 600;
        }
        .search-results {
            padding: 15px;
            background: #1a1a2e;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 2px solid #2a4a6e;
        }
        .search-results strong {
            color: #a0c4ff;
        }
        """
    
    def _section_executive_summary(self):
        """Section 1: Executive Summary with visual stats."""
        code_freq = self._get_code_frequency()
        total_codes = sum(code_freq.values())
        unique_codes = len(code_freq)
        avg_codes = total_codes / len(self.segments) if self.segments else 0
        
        html = f"""
        <section class="section" id="executive">
            <h2>Executive Summary</h2>
            <p>This report presents a comprehensive qualitative analysis of <em>{self.work.title}</em> by {self.work.author}, 
            using the {self.codebook.name} codebook. The analysis includes {len(self.segments)} coded segments 
            representing {total_codes} code applications across {unique_codes} distinct codes.</p>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{len(self.full_text):,}</div>
                    <div class="stat-label">Characters</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{len(self.segments)}</div>
                    <div class="stat-label">Coded Segments</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{unique_codes}</div>
                    <div class="stat-label">Unique Codes</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{total_codes}</div>
                    <div class="stat-label">Total Applications</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{avg_codes:.2f}</div>
                    <div class="stat-label">Avg Codes/Segment</div>
                </div>
            </div>
        </section>
        """
        return html
    
    def _section_statistical_analysis(self):
        """Section 2: Statistical Analysis (chi-square tests) with chart."""
        html = """
        <section class="section" id="statistical">
            <h2>Statistical Analysis</h2>
            <p>Chi-square tests examine whether code pairs co-occur more or less frequently than expected by chance.</p>
        """
        
        # Get code pairs
        code_pairs = self._get_code_pairs()
        
        if code_pairs:
            # Prepare chart data
            sorted_pairs = sorted(code_pairs.items(), key=lambda x: x[1]['chi2'], reverse=True)[:15]
            pair_labels = [f"{code1} × {code2}" for (code1, code2), _ in sorted_pairs]
            chi2_values = [stats['chi2'] for _, stats in sorted_pairs]
            
            html += f"""
            <div class="chart-container">
                <canvas id="statisticalChart"></canvas>
            </div>
            
            <table class="sortable-table">
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
                        <td><strong>{code1}</strong> × <strong>{code2}</strong></td>
                        <td>{observed}</td>
                        <td>{expected:.2f}</td>
                        <td>{stats['chi2']:.4f}</td>
                        <td>{p_value:.4f}</td>
                        <td class="{sig_class}">{sig}</td>
                        <td>Co-occur <strong>{interpretation}</strong> than expected</td>
                    </tr>
                """
            
            html += f"""
                </tbody>
            </table>
            <p><small>* p &lt; 0.05, ** p &lt; 0.01, *** p &lt; 0.001</small></p>
            
            <script>
                const statCtx = document.getElementById('statisticalChart');
                new Chart(statCtx, {{
                    type: 'bar',
                    data: {{
                        labels: {json.dumps(pair_labels)},
                        datasets: [{{
                            label: 'Chi-square Value',
                            data: {json.dumps(chi2_values)},
                            backgroundColor: Array({len(chi2_values)}).fill(null).map((_, i) => 
                                i < 3 ? '#4a9' : i < 6 ? '#9a4' : '#417690'
                            ),
                            borderColor: '#2a2a2a',
                            borderWidth: 2,
                            borderRadius: 6
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{ display: false }},
                            title: {{
                                display: true,
                                text: 'Top 15 Code Pair Associations (Chi-square)',
                                color: '#a0c4ff',
                                font: {{ size: 16, weight: 'normal' }}
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                ticks: {{ color: '#888' }},
                                grid: {{ color: '#2a2a2a' }}
                            }},
                            x: {{
                                ticks: {{
                                    color: '#888',
                                    maxRotation: 45,
                                    minRotation: 45,
                                    font: {{ size: 10 }}
                                }},
                                grid: {{ display: false }}
                            }}
                        }}
                    }}
                }});
            </script>
            """
        else:
            html += "<p>Insufficient data for statistical analysis.</p>"
        
        html += "</section>"
        return html
    
    def _section_word_cloud(self):
        """Section 3: Word Cloud & Lexical Analysis with chart."""
        words = self._extract_words_from_segments()
        word_freq = Counter(words)
        top_words = word_freq.most_common(30)
        top_20 = word_freq.most_common(20)
        
        html = """
        <section class="section" id="word">
            <h2>Word Cloud & Lexical Analysis</h2>
            <p>Analysis of word frequency in coded segments (excluding stopwords, minimum 4 characters).</p>
        """
        
        if top_words:
            # Prepare chart data
            chart_labels = [word for word, _ in top_20]
            chart_data = [freq for _, freq in top_20]
            
            html += f"""
            <div class="chart-container">
                <canvas id="wordChart"></canvas>
            </div>
            
            <h3>Top 30 Words</h3>
            <table class="sortable-table">
                <thead>
                    <tr>
                        <th>Word</th>
                        <th>Frequency</th>
                        <th>Visualization</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            max_freq = top_words[0][1]
            
            for word, freq in top_words:
                bar_width = (freq / max_freq) * 100
                html += f"""
                        <tr>
                            <td><strong>{word}</strong></td>
                            <td>{freq}</td>
                            <td><div class="frequency-bar" style="width: {bar_width}%;"></div></td>
                        </tr>
                """
            
            html += f"""
                    </tbody>
                </table>
                
                <script>
                    const wordCtx = document.getElementById('wordChart');
                    new Chart(wordCtx, {{
                        type: 'bar',
                        data: {{
                            labels: {json.dumps(chart_labels)},
                            datasets: [{{
                                label: 'Word Frequency',
                                data: {json.dumps(chart_data)},
                                backgroundColor: '#9a4',
                                borderColor: '#2a2a2a',
                                borderWidth: 2,
                                borderRadius: 6
                            }}]
                        }},
                        options: {{
                            indexAxis: 'y',
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {{
                                legend: {{ display: false }},
                                title: {{
                                    display: true,
                                    text: 'Top 20 Words (Horizontal Bar)',
                                    color: '#a0c4ff',
                                    font: {{ size: 16, weight: 'normal' }}
                                }}
                            }},
                            scales: {{
                                x: {{
                                    beginAtZero: true,
                                    ticks: {{ color: '#888' }},
                                    grid: {{ color: '#2a2a2a' }}
                                }},
                                y: {{
                                    ticks: {{
                                        color: '#888',
                                        font: {{ size: 11 }}
                                    }},
                                    grid: {{ display: false }}
                                }}
                            }}
                        }}
                    }});
                </script>
            """
        else:
            html += "<p>No words found in coded segments.</p>"
        
        html += "</section>"
        return html
    
    def _section_thematic_analysis(self):
        """Section 4: Thematic Analysis."""
        # Group codes by type
        themes = defaultdict(list)
        for code_name, code in self.codes.items():
            code_type = code.code_type or 'descriptive'  # Default to 'descriptive' if None
            themes[code_type].append(code_name)
        
        html = """
        <section class="section" id="thematic">
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
        <section class="section" id="codebook">
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
        """Section 6: Code Frequency Analysis with multiple chart types."""
        code_freq = self._get_code_frequency()
        sorted_codes = sorted(code_freq.items(), key=lambda x: x[1], reverse=True)
        max_freq = sorted_codes[0][1] if sorted_codes else 1
        
        # Prepare data for charts
        top_10 = sorted_codes[:10]
        top_15 = sorted_codes[:15]
        chart_labels = [code[0] for code in top_10]
        chart_data = [code[1] for code in top_10]
        pie_labels = [code[0] for code in top_15]
        pie_data = [code[1] for code in top_15]
        
        # Color palette
        chart_colors = [
            '#417690', '#5a8ba5', '#9a4', '#a0c4ff', '#4a9',
            '#aa4', '#8a6', '#6a8', '#7a5', '#5a7',
            '#8a4', '#6a6', '#7a7', '#5a5', '#9a9'
        ]
        
        html = f"""
        <section class="section" id="frequency">
            <h2>Code Frequency Analysis</h2>
            
            <div class="chart-wrapper">
                <div class="chart-card">
                    <canvas id="frequencyBarChart"></canvas>
                </div>
                <div class="chart-card">
                    <canvas id="frequencyPieChart"></canvas>
                </div>
            </div>
            
            <table class="sortable-table">
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
                        <td><strong>{code_name}</strong></td>
                        <td>{freq}</td>
                        <td>{percentage:.1f}%</td>
                        <td><div class="frequency-bar" style="width: {bar_width}%;"></div></td>
                    </tr>
            """
        
        html += f"""
                </tbody>
            </table>
            
            <script>
                // Bar Chart
                const barCtx = document.getElementById('frequencyBarChart');
                new Chart(barCtx, {{
                    type: 'bar',
                    data: {{
                        labels: {json.dumps(chart_labels)},
                        datasets: [{{
                            label: 'Frequency',
                            data: {json.dumps(chart_data)},
                            backgroundColor: {json.dumps(chart_colors[:len(chart_data)])},
                            borderColor: '#2a2a2a',
                            borderWidth: 2,
                            borderRadius: 8
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{ display: false }},
                            title: {{
                                display: true,
                                text: 'Top 10 Codes (Bar)',
                                color: '#a0c4ff',
                                font: {{ size: 16, weight: 'normal' }}
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                ticks: {{ color: '#888' }},
                                grid: {{ color: '#2a2a2a' }}
                            }},
                            x: {{
                                ticks: {{
                                    color: '#888',
                                    maxRotation: 45,
                                    minRotation: 45
                                }},
                                grid: {{ display: false }}
                            }}
                        }}
                    }}
                }});
                
                // Pie Chart
                const pieCtx = document.getElementById('frequencyPieChart');
                new Chart(pieCtx, {{
                    type: 'pie',
                    data: {{
                        labels: {json.dumps(pie_labels)},
                        datasets: [{{
                            data: {json.dumps(pie_data)},
                            backgroundColor: {json.dumps(chart_colors[:len(pie_data)])},
                            borderColor: '#0a0a0a',
                            borderWidth: 3
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                position: 'right',
                                labels: {{
                                    color: '#888',
                                    font: {{ size: 11 }},
                                    padding: 10
                                }}
                            }},
                            title: {{
                                display: true,
                                text: 'Top 15 Codes (Pie)',
                                color: '#a0c4ff',
                                font: {{ size: 16, weight: 'normal' }}
                            }}
                        }}
                    }}
                }});
            </script>
        </section>
        """
        return html
    
    def _section_co_occurrence(self):
        """Section 7: Co-occurrence Network."""
        html = """
        <section class="section" id="co-occurrence">
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
                code_type = code.code_type or 'descriptive'  # Default to 'descriptive' if None
                theme_segments[code_type].append((segment, code.code_name))
        
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
                code_types = [code.code_type or 'descriptive' for code in segment.codes.all() if code.code_type]
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
                code_types = [code.code_type or 'descriptive' for code in segment.codes.all() if code.code_type]
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
                    count = sum(1 for seg in group for code in seg.codes.all() if (code.code_type or 'descriptive') == code_type)
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
        """Section 14: Code Hierarchy Tree with proper parent-child relationships."""
        html = """
        <section class="section" id="hierarchy">
            <h2>Code Hierarchy Tree</h2>
            <p>Codes organized by type and hierarchy. Child codes are indented under their parent codes.</p>
            <div class="hierarchy-tree">
        """
        
        code_freq = self._get_code_frequency()
        
        # Build a proper tree structure
        def build_tree(codes_list):
            """Build a tree structure from codes."""
            # Find root codes (no parent)
            root_codes = [code for code in codes_list if code.parent_code is None]
            # Build a map of parent -> children
            children_map = defaultdict(list)
            for code in codes_list:
                if code.parent_code:
                    children_map[code.parent_code.pk].append(code)
            
            def render_code(code, level=0):
                """Recursively render a code and its children."""
                freq = code_freq.get(code.code_name, 0)
                indent = '<span class="tree-indent"></span>' * level
                bar_width = min(200, freq * 10) if freq > 0 else 0
                bar_html = f'<span style="display: inline-block; width: {bar_width}px; height: 12px; background: #417690; margin-left: 10px;"></span>' if bar_width > 0 else ''
                
                html_parts = [f"""
                <div class="tree-item" style="margin-left: {level * 25}px;">
                    {indent}<strong>{code.code_name}</strong> {bar_html}
                    <span style="color: #888; margin-left: 10px;">({freq})</span>
                </div>
                """]
                
                # Render children
                children = sorted(children_map.get(code.pk, []), key=lambda c: (c.order, c.code_name))
                for child in children:
                    html_parts.extend(render_code(child, level + 1))
                
                return html_parts
            
            # Render all root codes and their children
            result = []
            for root in sorted(root_codes, key=lambda c: (c.order, c.code_name)):
                result.extend(render_code(root, 0))
            
            return result
        
        # Group by type and build trees
        by_type = defaultdict(list)
        for code in self.codebook.codes.all():
            code_type = code.code_type or 'descriptive'  # Default to 'descriptive' if None
            by_type[code_type].append(code)
        
        for code_type, codes_list in sorted(by_type.items()):
            html += f'<div class="tree-item" style="margin-top: 20px; margin-bottom: 10px;"><strong style="font-size: 18px; color: #a0c4ff;">{code_type.upper()}</strong></div>'
            tree_items = build_tree(codes_list)
            html += ''.join(tree_items)
        
        html += """
            </div>
        </section>
        """
        return html
    
    def _section_complete_segments(self):
        """Section 15: Complete Coded Segment Catalog with search."""
        html = """
        <section class="section" id="segments">
            <h2>Complete Coded Segment Catalog</h2>
            <p>All coded segments with full context. Use the search box above to filter segments.</p>
            <div id="segment-count" style="margin-bottom: 20px; color: #888;"></div>
        """
        
        for i, segment in enumerate(self.segments, 1):
            code_names = ', '.join([c.code_name for c in segment.codes.all()])
            code_badges = ''.join([f'<span class="code-badge">{c.code_name}</span>' for c in segment.codes.all()])
            html += f"""
            <div class="segment-box" data-segment-index="{i}" data-codes="{code_names.lower()}" data-text="{segment.text_excerpt.lower()}">
                <div class="segment-text">"{segment.text_excerpt}"</div>
                <div style="margin: 15px 0;">
                    {code_badges}
                </div>
                <div class="segment-meta">
                    <strong>Segment {i}</strong> | 
                    Position: {segment.start_position}-{segment.end_position}
                    {f'<br><strong>Location:</strong> {segment.location}' if segment.location else ''}
                    {f'<br><strong>Memo:</strong> {segment.memo}' if segment.memo else ''}
                </div>
            </div>
            """
        
        html += """
            <script>
                // Update segment count
                function updateSegmentCount() {
                    const visible = document.querySelectorAll('.segment-box[style*="display: block"], .segment-box:not([style*="display: none"])').length;
                    const total = document.querySelectorAll('.segment-box').length;
                    document.getElementById('segment-count').textContent = `Showing ${visible} of ${total} segments`;
                }
                
                // Enhanced search for segments
                const searchInput = document.getElementById('search-input');
                const originalSearch = searchInput.oninput;
                searchInput.addEventListener('input', function(e) {
                    const searchTerm = e.target.value.toLowerCase();
                    const segments = document.querySelectorAll('.segment-box');
                    let visible = 0;
                    
                    segments.forEach(segment => {
                        const text = segment.dataset.text || '';
                        const codes = segment.dataset.codes || '';
                        if (text.includes(searchTerm) || codes.includes(searchTerm) || searchTerm === '') {
                            segment.style.display = 'block';
                            visible++;
                        } else {
                            segment.style.display = 'none';
                        }
                    });
                    
                    document.getElementById('segment-count').textContent = `Showing ${visible} of ${segments.length} segments`;
                });
                
                updateSegmentCount();
            </script>
        </section>
        """
        return html
    
    def _section_memos(self):
        """Section 16: Analytical Memos."""
        memos = self.analysis.memos.all()
        
        html = f"""
        <section class="section" id="memos">
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
            using the Qualitative Analysis for Literature Framework.</p>
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

