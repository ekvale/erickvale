"""
Views for literary analysis app.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db.models import Q
import json

from .models import LiteraryWork, CodebookTemplate, Code, Analysis, CodedSegment, AnalyticalMemo


def index(request):
    """Landing page for literary analysis app."""
    recent_works = LiteraryWork.objects.all()[:5]
    recent_analyses = Analysis.objects.all()[:5]
    codebooks = CodebookTemplate.objects.filter(is_public=True)[:5]
    
    context = {
        'recent_works': recent_works,
        'recent_analyses': recent_analyses,
        'codebooks': codebooks,
    }
    return render(request, 'literary_analysis/index.html', context)


class LiteraryWorkListView(ListView):
    """List all literary works."""
    model = LiteraryWork
    template_name = 'literary_analysis/work_list.html'
    context_object_name = 'works'
    paginate_by = 20


class LiteraryWorkDetailView(DetailView):
    """View details of a literary work."""
    model = LiteraryWork
    template_name = 'literary_analysis/work_detail.html'
    context_object_name = 'work'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['analyses'] = self.object.analyses.all()
        return context


@login_required
def upload_work(request):
    """Upload a new literary work."""
    if request.method == 'POST':
        title = request.POST.get('title')
        author = request.POST.get('author')
        text_file = request.FILES.get('text_file')
        
        if title and author and text_file:
            work = LiteraryWork.objects.create(
                title=title,
                author=author,
                text_file=text_file,
                uploaded_by=request.user
            )
            
            # Calculate text length
            try:
                with work.text_file.open('r', encoding='utf-8') as f:
                    text = f.read()
                    work.text_length = len(text)
                    work.save()
            except Exception as e:
                messages.warning(request, f'Could not calculate text length: {e}')
            
            messages.success(request, f'Successfully uploaded {work.title}')
            return redirect('literary_analysis:work_detail', pk=work.pk)
        else:
            messages.error(request, 'Please fill in all fields and upload a text file.')
    
    return render(request, 'literary_analysis/upload_work.html')


class CodebookListView(ListView):
    """List all codebook templates."""
    model = CodebookTemplate
    template_name = 'literary_analysis/codebook_list.html'
    context_object_name = 'codebooks'
    
    def get_queryset(self):
        queryset = CodebookTemplate.objects.all()
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_public=True)
        return queryset


class CodebookDetailView(DetailView):
    """View details of a codebook template."""
    model = CodebookTemplate
    template_name = 'literary_analysis/codebook_detail.html'
    context_object_name = 'codebook'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['codes'] = self.object.codes.all().order_by('order', 'code_name')
        return context


class AnalysisListView(ListView):
    """List all analyses."""
    model = Analysis
    template_name = 'literary_analysis/analysis_list.html'
    context_object_name = 'analyses'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Analysis.objects.all()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(analyst=self.request.user)
        return queryset


@login_required
def create_analysis(request):
    """Create a new analysis."""
    if request.method == 'POST':
        work_id = request.POST.get('literary_work')
        codebook_id = request.POST.get('codebook')
        
        if work_id and codebook_id:
            work = get_object_or_404(LiteraryWork, pk=work_id)
            codebook = get_object_or_404(CodebookTemplate, pk=codebook_id)
            
            analysis, created = Analysis.objects.get_or_create(
                literary_work=work,
                codebook=codebook,
                analyst=request.user,
                defaults={}
            )
            
            if created:
                messages.success(request, f'Created new analysis of {work.title}')
            else:
                messages.info(request, f'Using existing analysis of {work.title}')
            
            return redirect('literary_analysis:analysis_detail', pk=analysis.pk)
    
    works = LiteraryWork.objects.all()
    codebooks = CodebookTemplate.objects.filter(Q(is_public=True) | Q(created_by=request.user))
    
    context = {
        'works': works,
        'codebooks': codebooks,
    }
    return render(request, 'literary_analysis/create_analysis.html', context)


class AnalysisDetailView(DetailView):
    """View details of an analysis."""
    model = Analysis
    template_name = 'literary_analysis/analysis_detail.html'
    context_object_name = 'analysis'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['segments'] = self.object.coded_segments.all().order_by('start_position')
        context['memos'] = self.object.memos.all()
        context['code_frequency'] = self.object.get_code_frequency()
        return context


@login_required
def coding_interface(request, pk):
    """Coding interface for an analysis."""
    analysis = get_object_or_404(Analysis, pk=pk)
    
    # Check permissions
    if analysis.analyst != request.user and not request.user.is_superuser:
        messages.error(request, 'You do not have permission to code this analysis.')
        return redirect('literary_analysis:analysis_detail', pk=pk)
    
    # Get text content
    text_content = ""
    try:
        with analysis.literary_work.text_file.open('r', encoding='utf-8') as f:
            text_content = f.read()
    except Exception as e:
        messages.error(request, f'Error reading text file: {e}')
    
    context = {
        'analysis': analysis,
        'text_content': text_content,
        'codes': analysis.codebook.codes.all().order_by('order', 'code_name'),
        'segments': analysis.coded_segments.all().order_by('start_position'),
    }
    return render(request, 'literary_analysis/coding_interface.html', context)


@login_required
def analysis_dashboard(request, pk):
    """Analysis dashboard with statistics and visualizations."""
    analysis = get_object_or_404(Analysis, pk=pk)
    
    context = {
        'analysis': analysis,
        'code_frequency': analysis.get_code_frequency(),
        'segments': analysis.coded_segments.all(),
    }
    return render(request, 'literary_analysis/dashboard.html', context)


@login_required
@require_http_methods(["POST"])
def create_segment(request):
    """API endpoint to create a coded segment."""
    analysis_id = request.POST.get('analysis_id')
    start_pos = int(request.POST.get('start_position'))
    end_pos = int(request.POST.get('end_position'))
    code_ids = request.POST.getlist('codes')
    memo = request.POST.get('memo', '')
    location = request.POST.get('location', '')
    
    analysis = get_object_or_404(Analysis, pk=analysis_id)
    
    # Get text excerpt
    text_excerpt = analysis.literary_work.get_segment(start_pos, end_pos)
    
    segment = CodedSegment.objects.create(
        analysis=analysis,
        start_position=start_pos,
        end_position=end_pos,
        text_excerpt=text_excerpt,
        location=location,
        memo=memo,
        created_by=request.user
    )
    
    # Add codes
    for code_id in code_ids:
        try:
            code = Code.objects.get(pk=code_id, codebook=analysis.codebook)
            segment.codes.add(code)
        except Code.DoesNotExist:
            pass
    
    return JsonResponse({
        'success': True,
        'segment_id': segment.pk,
        'message': 'Segment created successfully'
    })


@login_required
@require_http_methods(["POST"])
def update_segment(request, pk):
    """API endpoint to update a coded segment."""
    segment = get_object_or_404(CodedSegment, pk=pk)
    
    if segment.created_by != request.user and not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    code_ids = request.POST.getlist('codes')
    memo = request.POST.get('memo', '')
    location = request.POST.get('location', '')
    
    segment.memo = memo
    segment.location = location
    segment.save()
    
    # Update codes
    segment.codes.clear()
    for code_id in code_ids:
        try:
            code = Code.objects.get(pk=code_id, codebook=segment.analysis.codebook)
            segment.codes.add(code)
        except Code.DoesNotExist:
            pass
    
    return JsonResponse({'success': True, 'message': 'Segment updated successfully'})


@login_required
@require_http_methods(["POST"])
def delete_segment(request, pk):
    """API endpoint to delete a coded segment."""
    segment = get_object_or_404(CodedSegment, pk=pk)
    
    if segment.created_by != request.user and not request.user.is_superuser:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    segment.delete()
    return JsonResponse({'success': True, 'message': 'Segment deleted successfully'})


@login_required
def generate_report(request, pk):
    """Generate comprehensive analysis report."""
    from django.utils import timezone
    from .reporting import ReportGenerator
    
    analysis = get_object_or_404(Analysis, pk=pk)
    
    # Get which sections to include
    include_sections = {
        'statistical': request.POST.get('include_statistical', 'on') == 'on',
        'word_cloud': request.POST.get('include_word_cloud', 'on') == 'on',
        'theme_excerpts': request.POST.get('include_theme_excerpts', 'on') == 'on',
        'progression': request.POST.get('include_progression', 'on') == 'on',
        'ngrams': request.POST.get('include_ngrams', 'on') == 'on',
        'comparative': request.POST.get('include_comparative', 'on') == 'on',
        'heatmap': request.POST.get('include_heatmap', 'on') == 'on',
        'sentiment': request.POST.get('include_sentiment', 'on') == 'on',
        'hierarchy': request.POST.get('include_hierarchy', 'on') == 'on',
    }
    
    try:
        generator = ReportGenerator(analysis)
        report_html = generator.generate_report(include_sections=include_sections)
        
        # Save report
        analysis.report_html = report_html
        analysis.report_generated_at = timezone.now()
        analysis.save()
        
        messages.success(request, 'Report generated successfully!')
        return redirect('literary_analysis:view_report', pk=pk)
    except Exception as e:
        messages.error(request, f'Error generating report: {str(e)}')
        return redirect('literary_analysis:analysis_detail', pk=pk)


@login_required
def view_report(request, pk):
    """View generated analysis report."""
    analysis = get_object_or_404(Analysis, pk=pk)
    
    if request.method == 'GET' and 'generate' in request.GET:
        # Show form to select report sections
        return render(request, 'literary_analysis/generate_report.html', {
            'analysis': analysis
        })
    
    if not analysis.report_html:
        messages.warning(request, 'No report generated yet. Please generate a report first.')
        return redirect('literary_analysis:generate_report', pk=pk)
    
    return HttpResponse(analysis.report_html)
