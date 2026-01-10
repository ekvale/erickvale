"""
Market simulation utilities for Tanzania mango market.
Simulates market forces between fresh and dried mango sales.
"""
import random
import math
from datetime import datetime, timedelta

# Exchange rate: 1 USD = 2,500 TZS (approximate rate as of 2025)
TZS_TO_USD_RATE = 0.0004  # 1 TZS = 0.0004 USD
USD_TO_TZS_RATE = 2500    # 1 USD = 2,500 TZS


def tzs_to_usd(tzs_amount):
    """Convert Tanzanian Shillings to US Dollars."""
    if tzs_amount is None:
        return None
    return round(float(tzs_amount) * TZS_TO_USD_RATE, 2)


def usd_to_tzs(usd_amount):
    """Convert US Dollars to Tanzanian Shillings."""
    if usd_amount is None:
        return None
    return round(float(usd_amount) * USD_TO_TZS_RATE, 0)


def generate_fresh_mango_prices(days=30, base_price=1500):
    """
    Generate realistic fresh mango prices in Tanzanian Shillings (TZS).
    
    Factors:
    - Seasonal variation (peak season has lower prices due to oversupply)
    - Day of week variation (weekend markets have higher prices)
    - Random volatility
    """
    prices = []
    base = base_price  # Base price in TZS per kg
    
    for day in range(days):
        # Day of week effect (weekends = higher prices)
        day_of_week = day % 7
        weekend_factor = 1.15 if day_of_week >= 5 else 1.0
        
        # Seasonal decline (prices drop as season progresses)
        seasonal_factor = 1.0 - (day * 0.008)  # Gradual decline
        
        # Random market volatility (±10%)
        volatility = random.uniform(0.90, 1.10)
        
        # Market saturation effect (more supply = lower price)
        saturation = 1.0 + (day * 0.003)  # Supply increases over time
        
        price = base * weekend_factor * seasonal_factor * volatility / saturation
        prices.append({
            'day': day + 1,
            'price': round(price, 2),
            'date': (datetime.now() - timedelta(days=days-day)).strftime('%Y-%m-%d')
        })
    
    return prices


def generate_dried_mango_prices(days=30, base_price=8000):
    """
    Generate realistic dried mango prices in Tanzanian Shillings (TZS).
    
    Dried mangoes have more stable prices but higher base cost.
    Factors:
    - More stable pricing (less volatility)
    - Premium pricing
    - Storage and processing costs reflected
    """
    prices = []
    base = base_price  # Base price in TZS per kg (dried)
    
    for day in range(days):
        # Less volatility than fresh
        volatility = random.uniform(0.95, 1.05)
        
        # Slight premium increase over time (scarcity in off-season)
        scarcity_factor = 1.0 + (day * 0.002)
        
        price = base * volatility * scarcity_factor
        prices.append({
            'day': day + 1,
            'price': round(price, 2),
            'date': (datetime.now() - timedelta(days=days-day)).strftime('%Y-%m-%d')
        })
    
    return prices


def calculate_fresh_mango_revenue(quantity_kg, price_per_kg, transport_cost_per_kg=200, 
                                   spoilage_rate=0.15, market_fees=0.05):
    """
    Calculate revenue from selling fresh mangoes.
    
    Args:
        quantity_kg: Total quantity in kg
        price_per_kg: Selling price per kg
        transport_cost_per_kg: Transportation cost (TZS/kg)
        spoilage_rate: Percentage lost to spoilage (0-1)
        market_fees: Market/trading fees as percentage (0-1)
    """
    # Calculate losses
    spoilage_loss = quantity_kg * spoilage_rate
    sellable_quantity = quantity_kg - spoilage_loss
    
    # Calculate revenue
    gross_revenue = sellable_quantity * price_per_kg
    
    # Deduct costs
    transport_cost = quantity_kg * transport_cost_per_kg  # Pay for transport even on spoiled goods
    market_fees_cost = gross_revenue * market_fees
    
    net_revenue = gross_revenue - transport_cost - market_fees_cost
    
    return {
        'quantity_kg': quantity_kg,
        'sellable_quantity_kg': sellable_quantity,
        'spoilage_kg': spoilage_loss,
        'spoilage_rate': spoilage_rate,
        'gross_revenue': round(gross_revenue, 2),
        'transport_cost': round(transport_cost, 2),
        'market_fees': round(market_fees_cost, 2),
        'net_revenue': round(net_revenue, 2),
        'price_per_kg': price_per_kg
    }


def calculate_dried_mango_revenue(quantity_kg_fresh, fresh_price_per_kg,
                                   drying_cost_per_kg=500, equipment_depreciation=0.02,
                                   storage_cost_per_month=300, processing_time_days=7,
                                   market_fees=0.03, shrinkage_rate=0.85):
    """
    Calculate revenue from selling dried mangoes.
    
    Args:
        quantity_kg_fresh: Initial fresh quantity in kg
        fresh_price_per_kg: Opportunity cost (fresh price)
        drying_cost_per_kg: Cost per kg to dry (labor, fuel, etc.)
        equipment_depreciation: Equipment cost as % of value
        storage_cost_per_month: Monthly storage cost per kg
        processing_time_days: Days to process (affects storage)
        market_fees: Market/trading fees
        shrinkage_rate: Weight after drying (0.85 = 85% weight loss, 15% yield)
    """
    # Calculate dried quantity (significant weight loss)
    dried_quantity = quantity_kg_fresh * (1 - shrinkage_rate)
    
    # Dried mangoes sell at premium
    dried_price_per_kg = 8000  # Premium price for dried
    
    # Gross revenue
    gross_revenue = dried_quantity * dried_price_per_kg
    
    # Calculate costs
    opportunity_cost = quantity_kg_fresh * fresh_price_per_kg  # Could have sold fresh
    drying_cost = quantity_kg_fresh * drying_cost_per_kg
    storage_cost = (quantity_kg_fresh * storage_cost_per_month * processing_time_days) / 30
    equipment_cost = gross_revenue * equipment_depreciation
    market_fees_cost = gross_revenue * market_fees
    
    total_costs = opportunity_cost + drying_cost + storage_cost + equipment_cost + market_fees_cost
    
    net_revenue = gross_revenue - total_costs
    
    return {
        'quantity_fresh_kg': quantity_kg_fresh,
        'quantity_dried_kg': round(dried_quantity, 2),
        'shrinkage_rate': shrinkage_rate,
        'gross_revenue': round(gross_revenue, 2),
        'opportunity_cost': round(opportunity_cost, 2),
        'drying_cost': round(drying_cost, 2),
        'storage_cost': round(storage_cost, 2),
        'equipment_cost': round(equipment_cost, 2),
        'market_fees': round(market_fees_cost, 2),
        'total_costs': round(total_costs, 2),
        'net_revenue': round(net_revenue, 2),
        'price_per_kg_fresh': fresh_price_per_kg,
        'price_per_kg_dried': dried_price_per_kg,
        'processing_days': processing_time_days
    }


def run_market_simulation(quantity_kg=1000, days=30):
    """
    Run complete market simulation comparing fresh vs dried strategies.
    
    Args:
        quantity_kg: Total mango quantity in kg
        days: Number of days to simulate
    """
    # Generate price data
    fresh_prices = generate_fresh_mango_prices(days=days)
    dried_prices = generate_dried_mango_prices(days=days)
    
    # Calculate average prices
    avg_fresh_price = sum(p['price'] for p in fresh_prices) / len(fresh_prices)
    avg_dried_price = sum(p['price'] for p in dried_prices) / len(dried_prices)
    
    # Scenario 1: Sell all fresh
    fresh_revenue = calculate_fresh_mango_revenue(
        quantity_kg=quantity_kg,
        price_per_kg=avg_fresh_price
    )
    
    # Scenario 2: Dry all mangoes
    dried_revenue = calculate_dried_mango_revenue(
        quantity_kg_fresh=quantity_kg,
        fresh_price_per_kg=avg_fresh_price
    )
    
    # Scenario 3: Hybrid strategy (50/50 split)
    hybrid_fresh = calculate_fresh_mango_revenue(
        quantity_kg=quantity_kg * 0.5,
        price_per_kg=avg_fresh_price
    )
    hybrid_dried = calculate_dried_mango_revenue(
        quantity_kg_fresh=quantity_kg * 0.5,
        fresh_price_per_kg=avg_fresh_price
    )
    hybrid_total = hybrid_fresh['net_revenue'] + hybrid_dried['net_revenue']
    
    # Market analysis
    price_volatility_fresh = calculate_volatility([p['price'] for p in fresh_prices])
    price_volatility_dried = calculate_volatility([p['price'] for p in dried_prices])
    
    # Break-even analysis
    breakeven_fresh_price = calculate_breakeven_fresh_price(quantity_kg)
    breakeven_dried_price = calculate_breakeven_dried_price(quantity_kg, avg_fresh_price)
    
    return {
        'fresh_prices': fresh_prices,
        'dried_prices': dried_prices,
        'avg_fresh_price': round(avg_fresh_price, 2),
        'avg_dried_price': round(avg_dried_price, 2),
        'fresh_strategy': fresh_revenue,
        'dried_strategy': dried_revenue,
        'hybrid_strategy': {
            'fresh': hybrid_fresh,
            'dried': hybrid_dried,
            'total_net_revenue': round(hybrid_total, 2)
        },
        'profitability_comparison': {
            'fresh_net_revenue': fresh_revenue['net_revenue'],
            'dried_net_revenue': dried_revenue['net_revenue'],
            'hybrid_net_revenue': round(hybrid_total, 2),
            'best_strategy': max(
                ('Fresh', fresh_revenue['net_revenue']),
                ('Dried', dried_revenue['net_revenue']),
                ('Hybrid', round(hybrid_total, 2)),
                key=lambda x: x[1]
            )[0],
            'profit_difference': round(
                max(dried_revenue['net_revenue'], fresh_revenue['net_revenue']) - 
                min(dried_revenue['net_revenue'], fresh_revenue['net_revenue']), 
                2
            )
        },
        'price_trends': {
            'fresh_prices': fresh_prices,
            'dried_prices': dried_prices,
            'fresh_volatility': round(price_volatility_fresh, 2),
            'dried_volatility': round(price_volatility_dried, 2)
        },
        'market_analysis': {
            'breakeven_fresh_price': round(breakeven_fresh_price, 2),
            'breakeven_dried_price': round(breakeven_dried_price, 2),
            'current_fresh_price': round(avg_fresh_price, 2),
            'current_dried_price': round(avg_dried_price, 2),
            'fresh_price_advantage': round(avg_fresh_price - breakeven_fresh_price, 2),
            'dried_price_advantage': round(avg_dried_price - breakeven_dried_price, 2),
            'recommendation': generate_recommendation(
                fresh_revenue['net_revenue'],
                dried_revenue['net_revenue'],
                price_volatility_fresh,
                price_volatility_dried
            )
        },
        'simulation_parameters': {
            'quantity_kg': quantity_kg,
            'days': days,
            'region': 'Tanzania',
            'currency': 'TZS (Tanzanian Shillings)'
        }
    }


def calculate_volatility(prices):
    """Calculate price volatility (coefficient of variation)."""
    if not prices:
        return 0
    mean = sum(prices) / len(prices)
    variance = sum((p - mean) ** 2 for p in prices) / len(prices)
    std_dev = math.sqrt(variance)
    return (std_dev / mean) * 100 if mean > 0 else 0


def calculate_breakeven_fresh_price(quantity_kg, transport_cost=200, spoilage_rate=0.15, market_fees=0.05):
    """Calculate minimum fresh price needed to break even."""
    # Solve: net_revenue = 0
    # gross_revenue - transport - fees = 0
    # sellable * price - transport - gross_revenue * fees = 0
    # sellable * price - transport - sellable * price * fees = 0
    # sellable * price * (1 - fees) = transport
    # price = transport / (sellable * (1 - fees))
    
    sellable = quantity_kg * (1 - spoilage_rate)
    transport_total = quantity_kg * transport_cost
    
    if sellable * (1 - market_fees) == 0:
        return 0
    
    breakeven = transport_total / (sellable * (1 - market_fees))
    return breakeven


def calculate_breakeven_dried_price(quantity_fresh, fresh_price, shrinkage=0.85, 
                                     drying_cost=500, storage=300, processing_days=7,
                                     equipment_dep=0.02, market_fees=0.03):
    """Calculate minimum dried price needed to break even."""
    dried_quantity = quantity_fresh * (1 - shrinkage)
    
    # Total costs
    opportunity = quantity_fresh * fresh_price
    drying = quantity_fresh * drying_cost
    storage_total = (quantity_fresh * storage * processing_days) / 30
    
    # Breakeven: gross_revenue - costs - market_fees - equipment = 0
    # gross_revenue * (1 - fees - equipment_dep) = other_costs
    # dried_quantity * price * (1 - fees - equipment_dep) = other_costs
    # price = other_costs / (dried_quantity * (1 - fees - equipment_dep))
    
    other_costs = opportunity + drying + storage_total
    denominator = dried_quantity * (1 - market_fees - equipment_dep)
    
    if denominator == 0:
        return 0
    
    breakeven = other_costs / denominator
    return breakeven


def generate_recommendation(fresh_revenue, dried_revenue, fresh_volatility, dried_volatility):
    """Generate market recommendation based on analysis."""
    revenue_diff = dried_revenue - fresh_revenue
    volatility_diff = fresh_volatility - dried_volatility
    
    if revenue_diff > 500000:  # Significant profit difference
        if revenue_diff > 0:
            return {
                'strategy': 'Dried',
                'reason': f'Drying yields {revenue_diff:,.0f} TZS more profit with {volatility_diff:.1f}% lower price volatility.'
            }
        else:
            return {
                'strategy': 'Fresh',
                'reason': f'Fresh sales yield {abs(revenue_diff):,.0f} TZS more profit, ideal for immediate cash flow.'
            }
    else:
        if volatility_diff > 5:
            return {
                'strategy': 'Hybrid',
                'reason': 'Similar profitability. Hybrid strategy reduces risk by diversifying between stable (dried) and variable (fresh) markets.'
            }
        else:
            return {
                'strategy': 'Fresh',
                'reason': 'Similar profitability and volatility. Fresh sales recommended for lower initial investment and faster returns.'
            }
