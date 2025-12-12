"""
Management command to generate analysis reports from command line.
This avoids timeout issues with web requests.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from literary_analysis.models import Analysis
from literary_analysis.reporting import ReportGenerator


class Command(BaseCommand):
    help = 'Generate comprehensive report for an analysis'

    def add_arguments(self, parser):
        parser.add_argument(
            'analysis_id',
            type=int,
            help='ID of the analysis to generate report for'
        )
        parser.add_argument(
            '--include-all',
            action='store_true',
            help='Include all report sections (default: all sections included)'
        )
        parser.add_argument(
            '--skip-statistical',
            action='store_true',
            help='Skip statistical analysis section (faster)'
        )

    def handle(self, *args, **options):
        analysis_id = options['analysis_id']
        
        try:
            analysis = Analysis.objects.get(pk=analysis_id)
        except Analysis.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Analysis with ID {analysis_id} not found.'))
            return
        
        self.stdout.write(f'Generating report for: {analysis.literary_work.title}')
        self.stdout.write(f'Codebook: {analysis.codebook.name}')
        self.stdout.write(f'Segments: {analysis.coded_segments.count()}')
        self.stdout.write('')
        
        # Determine which sections to include
        include_sections = {
            'statistical': not options['skip_statistical'],
            'word_cloud': True,
            'theme_excerpts': True,
            'progression': True,
            'ngrams': True,
            'comparative': True,
            'heatmap': True,
            'sentiment': True,
            'hierarchy': True,
        }
        
        try:
            self.stdout.write('Starting report generation...')
            generator = ReportGenerator(analysis)
            
            self.stdout.write('  - Generating report sections...')
            report_html = generator.generate_report(include_sections=include_sections)
            
            self.stdout.write('  - Saving report to database...')
            analysis.report_html = report_html
            analysis.report_generated_at = timezone.now()
            analysis.save()
            
            self.stdout.write(self.style.SUCCESS('\n✓ Report generated successfully!'))
            self.stdout.write(f'  Report size: {len(report_html):,} characters')
            self.stdout.write(f'  View at: /apps/literary/analyses/{analysis.pk}/report/')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error generating report: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
            return
