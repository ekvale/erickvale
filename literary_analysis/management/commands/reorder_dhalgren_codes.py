"""
Management command to reorder Dhalgren codes in a logical way.
"""
from django.core.management.base import BaseCommand
from literary_analysis.models import CodebookTemplate, Code


class Command(BaseCommand):
    help = 'Reorder Dhalgren codes in a logical sequence'

    def handle(self, *args, **options):
        # Get the Dhalgren codebook
        try:
            codebook = CodebookTemplate.objects.get(name='Dhalgren - Complete Analysis')
        except CodebookTemplate.DoesNotExist:
            self.stdout.write(self.style.ERROR('Codebook "Dhalgren - Complete Analysis" not found.'))
            return
        
        # Define logical order for codes
        # Grouped by theme: Setting -> Physical -> Social -> Reality/Time
        logical_order = [
            # Setting/Place codes
            'BELLONA_CITY',           # 0: The city itself
            'ARCHITECTURE',           # 1: Buildings/structures
            'SPATIAL_DISORIENTATION', # 2: Spatial confusion
            
            # Physical/Descriptive codes
            'URBAN_DECAY',            # 3: Decay/ruins
            'FIRE_DESTRUCTION',       # 4: Fire/destruction
            
            # Social codes
            'SOCIAL_COLLAPSE',        # 5: Social breakdown
            
            # Reality/Time codes
            'TEMPORAL_ANOMALY',       # 6: Time behaving strangely
            'REALITY_BREAK',          # 7: Reality/logic breaking down
        ]
        
        # Update order for each code
        updated_count = 0
        for order_value, code_name in enumerate(logical_order):
            try:
                code = Code.objects.get(codebook=codebook, code_name=code_name)
                old_order = code.order
                code.order = order_value
                code.save()
                updated_count += 1
                self.stdout.write(
                    f'  {code_name}: {old_order} -> {order_value}'
                )
            except Code.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'  Code "{code_name}" not found, skipping')
                )
        
        # Also update any other codes that might exist to have higher order values
        # so they appear after the main codes
        other_codes = Code.objects.filter(codebook=codebook).exclude(code_name__in=logical_order)
        base_order = len(logical_order)
        for idx, code in enumerate(other_codes.order_by('order', 'code_name')):
            code.order = base_order + idx
            code.save()
            updated_count += 1
            self.stdout.write(
                f'  {code.code_name}: -> {code.order} (other code)'
            )
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully reordered {updated_count} codes!'))
        self.stdout.write(self.style.SUCCESS(f'  Codes are now ordered logically by theme.'))

