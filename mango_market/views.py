from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils.safestring import mark_safe
from django.db.models import Avg, Max, Min, Count
from .models import MarketSimulation
from .utils import run_market_simulation, tzs_to_usd
import json


def index(request):
    """Main view for mango market simulation."""
    # Get parameters from request or use defaults
    quantity = int(request.GET.get('quantity', 1000))
    days = int(request.GET.get('days', 30))
    save = request.GET.get('save', 'true').lower() != 'false'  # Save by default
    
    # Run simulation
    simulation_data = run_market_simulation(quantity_kg=quantity, days=days)
    
    # Save simulation to database if requested
    simulation = None
    if save:
        simulation = MarketSimulation.objects.create(
            quantity_kg=quantity,
            simulation_days=days,
            simulation_data=simulation_data,
            season="Peak Season",
            region="Tanzania"
        )
        # Extract and save summary metrics
        profitability = simulation_data.get('profitability_comparison', {})
        simulation.fresh_net_revenue = profitability.get('fresh_net_revenue') or simulation_data.get('fresh_strategy', {}).get('net_revenue', 0)
        simulation.dried_net_revenue = profitability.get('dried_net_revenue') or simulation_data.get('dried_strategy', {}).get('net_revenue', 0)
        simulation.hybrid_net_revenue = profitability.get('hybrid_net_revenue') or simulation_data.get('hybrid_strategy', {}).get('total_net_revenue', 0)
        simulation.best_strategy = profitability.get('best_strategy', '')
        simulation.avg_fresh_price = simulation_data.get('avg_fresh_price', 0)
        simulation.avg_dried_price = simulation_data.get('avg_dried_price', 0)
        simulation.save()
    
    # Prepare JSON strings for template
    fresh_prices_json = json.dumps(simulation_data['fresh_prices'])
    dried_prices_json = json.dumps(simulation_data['dried_prices'])
    
    # Calculate percentages for template
    spoilage_percent = simulation_data['fresh_strategy']['spoilage_rate'] * 100
    shrinkage_percent = simulation_data['dried_strategy']['shrinkage_rate'] * 100
    
    # Add USD conversions for key values
    context = {
        'simulation': simulation,
        'data': simulation_data,
        'quantity': quantity,
        'days': days,
        'fresh_prices_json': mark_safe(fresh_prices_json),
        'dried_prices_json': mark_safe(dried_prices_json),
        'spoilage_percent': spoilage_percent,
        'shrinkage_percent': shrinkage_percent,
        'tzs_to_usd_rate': tzs_to_usd,
    }
    
    return render(request, 'mango_market/index.html', context)


def results(request):
    """View to display all historical simulation results and data."""
    # Get filter parameters
    season = request.GET.get('season', '')
    region = request.GET.get('region', '')
    strategy = request.GET.get('strategy', '')
    
    # Base queryset
    simulations = MarketSimulation.objects.filter(is_saved=True)
    
    # Apply filters
    if season:
        simulations = simulations.filter(season__icontains=season)
    if region:
        simulations = simulations.filter(region__icontains=region)
    if strategy:
        simulations = simulations.filter(best_strategy__iexact=strategy)
    
    # Get aggregate statistics
    stats = simulations.aggregate(
        total_simulations=Count('id'),
        avg_fresh_revenue=Avg('fresh_net_revenue'),
        avg_dried_revenue=Avg('dried_net_revenue'),
        max_fresh_revenue=Max('fresh_net_revenue'),
        max_dried_revenue=Max('dried_net_revenue'),
        min_fresh_price=Min('avg_fresh_price'),
        max_fresh_price=Max('avg_fresh_price'),
        min_dried_price=Min('avg_dried_price'),
        max_dried_price=Max('avg_dried_price'),
    )
    
    # Strategy distribution
    strategy_counts = {}
    for sim in simulations:
        strategy = sim.best_strategy or 'Unknown'
        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
    
    # Prepare data for charts
    recent_simulations = simulations[:50]  # Last 50 simulations for charts
    
    # Aggregate price trends over time (group by date)
    price_trends_data = {
        'dates': [],
        'fresh_prices': [],
        'dried_prices': [],
        'fresh_revenues': [],
        'dried_revenues': [],
    }
    
    for sim in recent_simulations:
        price_trends_data['dates'].append(sim.created_at.strftime('%Y-%m-%d'))
        if sim.avg_fresh_price:
            price_trends_data['fresh_prices'].append(float(sim.avg_fresh_price))
        if sim.avg_dried_price:
            price_trends_data['dried_prices'].append(float(sim.avg_dried_price))
        if sim.fresh_net_revenue:
            price_trends_data['fresh_revenues'].append(float(sim.fresh_net_revenue))
        if sim.dried_net_revenue:
            price_trends_data['dried_revenues'].append(float(sim.dried_net_revenue))
    
    context = {
        'simulations': simulations[:100],  # Show latest 100
        'stats': stats,
        'strategy_counts': strategy_counts,
        'price_trends_json': mark_safe(json.dumps(price_trends_data)),
        'season_filter': season,
        'region_filter': region,
        'strategy_filter': strategy,
        'total_count': simulations.count(),
    }
    
    return render(request, 'mango_market/results.html', context)


def simulation_detail(request, simulation_id):
    """View individual simulation details."""
    simulation = get_object_or_404(MarketSimulation, id=simulation_id, is_saved=True)
    
    # Prepare JSON strings for template
    fresh_prices_json = json.dumps(simulation.simulation_data.get('fresh_prices', []))
    dried_prices_json = json.dumps(simulation.simulation_data.get('dried_prices', []))
    
    context = {
        'simulation': simulation,
        'data': simulation.simulation_data,
        'fresh_prices_json': mark_safe(fresh_prices_json),
        'dried_prices_json': mark_safe(dried_prices_json),
    }
    
    return render(request, 'mango_market/simulation_detail.html', context)


def api_simulation_data(request):
    """API endpoint to get simulation data as JSON."""
    quantity = int(request.GET.get('quantity', 1000))
    days = int(request.GET.get('days', 30))
    
    simulation_data = run_market_simulation(quantity_kg=quantity, days=days)
    
    return JsonResponse(simulation_data, safe=False)
