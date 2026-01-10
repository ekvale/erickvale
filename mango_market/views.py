from django.shortcuts import render
from django.http import JsonResponse
from django.utils.safestring import mark_safe
from .models import MarketSimulation
from .utils import run_market_simulation
import json


def index(request):
    """Main view for mango market simulation."""
    # Get or create latest simulation
    simulation = MarketSimulation.objects.first()
    
    # Get parameters from request or use defaults
    quantity = int(request.GET.get('quantity', 1000))
    days = int(request.GET.get('days', 30))
    
    # Run simulation
    simulation_data = run_market_simulation(quantity_kg=quantity, days=days)
    
    # Save simulation to database
    if simulation:
        simulation.simulation_data = simulation_data
        simulation.save()
    else:
        simulation = MarketSimulation.objects.create(
            simulation_data=simulation_data,
            season="Peak Season",
            region="Tanzania"
        )
    
    # Prepare JSON strings for template
    fresh_prices_json = json.dumps(simulation_data['fresh_prices'])
    dried_prices_json = json.dumps(simulation_data['dried_prices'])
    
    # Calculate percentages for template
    spoilage_percent = simulation_data['fresh_strategy']['spoilage_rate'] * 100
    shrinkage_percent = simulation_data['dried_strategy']['shrinkage_rate'] * 100
    
    context = {
        'simulation': simulation,
        'data': simulation_data,
        'quantity': quantity,
        'days': days,
        'fresh_prices_json': mark_safe(fresh_prices_json),
        'dried_prices_json': mark_safe(dried_prices_json),
        'spoilage_percent': spoilage_percent,
        'shrinkage_percent': shrinkage_percent,
    }
    
    return render(request, 'mango_market/index.html', context)


def api_simulation_data(request):
    """API endpoint to get simulation data as JSON."""
    quantity = int(request.GET.get('quantity', 1000))
    days = int(request.GET.get('days', 30))
    
    simulation_data = run_market_simulation(quantity_kg=quantity, days=days)
    
    return JsonResponse(simulation_data, safe=False)
