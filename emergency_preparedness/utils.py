"""
Utility functions for emergency preparedness calculations.
Includes boundary validation, risk calculations, drive time, and optimization algorithms.
"""
import json
import math
import os
from typing import List, Dict, Tuple, Optional
from decimal import Decimal
import requests
from decouple import config


# Minnesota boundary constraints
MINNESOTA_BOUNDS = {
    'min_lat': 43.0,
    'max_lat': 49.5,
    'min_lon': -97.5,
    'max_lon': -89.0,
}


def constrain_to_minnesota(latitude: float, longitude: float) -> Tuple[float, float]:
    """
    Constrain coordinates to Minnesota boundaries.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
    
    Returns:
        Tuple of (constrained_latitude, constrained_longitude)
    """
    lat = max(MINNESOTA_BOUNDS['min_lat'], min(MINNESOTA_BOUNDS['max_lat'], latitude))
    lon = max(MINNESOTA_BOUNDS['min_lon'], min(MINNESOTA_BOUNDS['max_lon'], longitude))
    return lat, lon


def is_in_minnesota(latitude: float, longitude: float) -> bool:
    """
    Check if coordinates are within Minnesota boundaries.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
    
    Returns:
        True if coordinates are within Minnesota, False otherwise
    """
    return (MINNESOTA_BOUNDS['min_lat'] <= latitude <= MINNESOTA_BOUNDS['max_lat'] and
            MINNESOTA_BOUNDS['min_lon'] <= longitude <= MINNESOTA_BOUNDS['max_lon'])


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth using Haversine formula.
    
    Args:
        lat1, lon1: Latitude and longitude of first point
        lat2, lon2: Latitude and longitude of second point
    
    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth's radius in kilometers
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def calculate_drive_time(lat1: float, lon1: float, lat2: float, lon2: float,
                        use_api: bool = True) -> float:
    """
    Calculate drive time between two points.
    
    Uses OpenRouteService API if available, otherwise falls back to distance-based estimation.
    
    Args:
        lat1, lon1: Starting point coordinates
        lat2, lon2: Destination point coordinates
        use_api: Whether to attempt API call (default: True)
    
    Returns:
        Drive time in minutes
    """
    if use_api:
        api_key = config('ORS_API_KEY', default=None)
        if api_key:
            try:
                url = "https://api.openrouteservice.org/v2/directions/driving-car"
                headers = {
                    'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
                    'Authorization': api_key,
                    'Content-Type': 'application/json; charset=utf-8'
                }
                body = {
                    "coordinates": [[lon1, lat1], [lon2, lat2]]
                }
                
                response = requests.post(url, json=body, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'routes' in data and len(data['routes']) > 0:
                        duration = data['routes'][0]['summary']['duration']  # in seconds
                        return duration / 60.0  # convert to minutes
            except Exception:
                pass  # Fall through to distance-based calculation
    
    # Fallback: distance-based estimation
    distance = haversine_distance(lat1, lon1, lat2, lon2)
    avg_speed = 60  # km/h
    time_hours = distance / avg_speed
    return time_hours * 60  # convert to minutes


def load_demographic_data() -> List[Dict]:
    """
    Load demographic data from JSON file.
    
    Returns:
        List of city dictionaries with name, lat, lon, population, county
    """
    json_path = os.path.join(os.path.dirname(__file__), 'demographic_data.json')
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return []


def calculate_risk_score(city_data: Dict) -> float:
    """
    Calculate risk score for a city based on demographic data.
    
    Formula: Risk = (Population Density/2000 × 0.4) + (Hazard × 0.3) + ((1-Infrastructure) × 0.3)
    
    Args:
        city_data: Dictionary with city information including population
    
    Returns:
        Risk score normalized to 0-1 range
    """
    population = city_data.get('population', 0)
    
    # Estimate area based on population (rough approximation)
    # Larger cities tend to have more area
    estimated_area_km2 = max(1.0, population / 500)  # Rough estimate
    population_density = population / estimated_area_km2 if estimated_area_km2 > 0 else 0
    
    # Normalize population density (assuming max density around 2000 per km2)
    density_score = min(1.0, population_density / 2000.0)
    
    # Generate hazard score based on population size
    # Larger populations = higher hazard potential
    hazard_score = min(1.0, population / 500000.0)
    
    # Generate infrastructure score (inverse - lower infrastructure = higher risk)
    # Smaller cities have lower infrastructure scores
    infrastructure_score = min(1.0, max(0.3, 1.0 - (population / 1000000.0)))
    
    # Calculate risk score
    risk = (density_score * 0.4) + (hazard_score * 0.3) + ((1 - infrastructure_score) * 0.3)
    
    # Normalize to 0-1 range
    return min(1.0, max(0.0, risk))


def apply_scenario_risk_modification(base_risk: float, city_data: Dict, scenario: Dict) -> float:
    """
    Apply scenario-specific risk modifications.
    
    Args:
        base_risk: Base risk score (0-1)
        city_data: City demographic data
        scenario: Scenario dictionary with type, severity, and affected_areas
    
    Returns:
        Modified risk score
    """
    scenario_type = scenario.get('type', 'general')
    severity = scenario.get('severity', 1.0)
    affected_areas = scenario.get('affected_areas', [])
    city_name = city_data.get('name', '')
    population = city_data.get('population', 0)
    
    if scenario_type == 'general':
        return base_risk
    
    # Calculate infrastructure score (same as in risk calculation)
    infrastructure_score = min(1.0, max(0.3, 1.0 - (population / 1000000.0)))
    
    if scenario_type == 'pandemic':
        # Affects all areas, more in high-density
        modification = 1 + (population / 500000.0) * severity
        return min(1.0, base_risk * modification)
    
    elif scenario_type == 'natural_disaster':
        # Only affects specified areas
        if affected_areas and city_name not in affected_areas:
            return base_risk
        modification = 1 + severity * 0.5
        return min(1.0, base_risk * modification)
    
    elif scenario_type == 'severe_weather':
        # Based on infrastructure vulnerability
        modification = 1 + (1 - infrastructure_score) * severity * 0.3
        return min(1.0, base_risk * modification)
    
    elif scenario_type == 'infrastructure_failure':
        # Significant impact on poor infrastructure areas
        modification = 1 + (1 - infrastructure_score) * severity * 0.4
        return min(1.0, base_risk * modification)
    
    return base_risk


def calculate_dynamic_radius(city_data: Dict, demographic_data: List[Dict]) -> float:
    """
    Calculate dynamic coverage radius based on population density and city characteristics.
    
    Args:
        city_data: City demographic data
        demographic_data: All demographic data for context
    
    Returns:
        Optimal radius in kilometers (20-80km range)
    """
    population = city_data.get('population', 0)
    
    # Estimate city area (rough approximation)
    estimated_area_km2 = max(1.0, population / 500)
    population_density = population / estimated_area_km2 if estimated_area_km2 > 0 else 0
    
    # Base radius on density
    # High density (urban): smaller radius (20-40km)
    # Medium density (suburban): medium radius (40-60km)
    # Low density (rural): larger radius (60-80km)
    
    if population_density > 1000:  # Urban
        base_radius = 30.0
    elif population_density > 200:  # Suburban
        base_radius = 50.0
    else:  # Rural
        base_radius = 70.0
    
    # Adjust based on city size
    if population > 100000:
        base_radius *= 0.8  # Large cities need more PODs, smaller radius
    elif population < 10000:
        base_radius *= 1.2  # Small cities can have larger radius
    
    # Clamp to 20-80km range
    return max(20.0, min(80.0, base_radius))


def estimate_pod_capacity(parking_lot_size: float, acreage: float, occupancy: int = 0) -> Dict:
    """
    Estimate POD capacity based on physical constraints.
    
    Args:
        parking_lot_size: Parking lot size in acres
        acreage: Total acreage
        occupancy: Current occupancy limit
    
    Returns:
        Dictionary with capacity estimates
    """
    # Estimate vehicles per day based on parking
    # Assume 1 vehicle per 200 sq ft (0.0046 acres), 2-hour processing time
    # 12 hours operation = 6 cycles per day
    if parking_lot_size > 0:
        vehicle_capacity = int((parking_lot_size / 0.0046) * 6)
    else:
        vehicle_capacity = 0
    
    # Estimate people capacity based on acreage
    # Assume 100 sq ft per person in processing area
    # 1 acre = 43,560 sq ft
    if acreage > 0:
        people_capacity = int((acreage * 43560) / 100)
    else:
        people_capacity = 0
    
    # Use occupancy if provided, otherwise estimate
    if occupancy > 0:
        daily_capacity = occupancy
    else:
        # Estimate: assume 2 people per vehicle, or acreage-based
        daily_capacity = max(vehicle_capacity * 2, people_capacity)
    
    return {
        'daily_capacity': daily_capacity,
        'vehicle_capacity': vehicle_capacity,
        'people_capacity': people_capacity,
    }


def calculate_infrastructure_score(city_data: Dict, demographic_data: List[Dict]) -> float:
    """
    Calculate infrastructure score for a location (0-1).
    
    Factors:
    - City size (larger = better infrastructure)
    - Population (more people = better facilities)
    - Proximity to major cities (better road access)
    
    Args:
        city_data: City demographic data
        demographic_data: All demographic data for context
    
    Returns:
        Infrastructure score (0-1)
    """
    population = city_data.get('population', 0)
    city_lat = city_data.get('lat', 0)
    city_lon = city_data.get('lon', 0)
    
    # Base score on city size
    if population > 100000:
        base_score = 0.9
    elif population > 50000:
        base_score = 0.7
    elif population > 20000:
        base_score = 0.5
    else:
        base_score = 0.3
    
    # Bonus for proximity to major cities (Minneapolis/St. Paul)
    minneapolis_lat, minneapolis_lon = 44.9778, -93.2650
    distance_to_msp = haversine_distance(city_lat, city_lon, minneapolis_lat, minneapolis_lon)
    
    if distance_to_msp < 50:  # Within 50km of MSP
        base_score += 0.1
    elif distance_to_msp < 100:  # Within 100km
        base_score += 0.05
    
    return min(1.0, base_score)


def calculate_vulnerability_score(city_data: Dict) -> float:
    """
    Estimate vulnerability score based on city characteristics.
    
    Higher score = more vulnerable population (elderly, low-income, limited access)
    
    Args:
        city_data: City demographic data
    
    Returns:
        Vulnerability multiplier (0-1, higher = more vulnerable)
    """
    population = city_data.get('population', 0)
    
    # Estimate vulnerability based on city size
    # Smaller cities often have:
    # - Higher elderly population percentage
    # - Limited public transit
    # - Fewer resources
    
    if population < 5000:
        vulnerability = 0.8  # Very vulnerable
    elif population < 20000:
        vulnerability = 0.6  # Moderately vulnerable
    elif population < 50000:
        vulnerability = 0.4  # Somewhat vulnerable
    else:
        vulnerability = 0.2  # Less vulnerable (more resources)
    
    return vulnerability


def calculate_pod_coverage(pod_lat: float, pod_lon: float, pod_radius: float,
                          demographic_data: List[Dict], scenario: Optional[Dict] = None,
                          existing_pods: Optional[List[Dict]] = None) -> Dict:
    """
    Calculate coverage statistics for a POD.
    
    Args:
        pod_lat: POD latitude
        pod_lon: POD longitude
        pod_radius: Coverage radius in kilometers
        demographic_data: List of city demographic data
        scenario: Optional scenario dictionary for risk modifications
        existing_pods: Optional list of existing PODs for redundancy calculation
    
    Returns:
        Dictionary with coverage statistics
    """
    points_covered = 0
    total_risk = 0.0
    total_population = 0
    vulnerable_population = 0
    drive_times = []
    overlap_population = 0  # Population already covered by other PODs
    
    for city in demographic_data:
        city_lat = city.get('lat')
        city_lon = city.get('lon')
        
        if city_lat is None or city_lon is None:
            continue
        
        distance = haversine_distance(pod_lat, pod_lon, city_lat, city_lon)
        
        if distance <= pod_radius:
            points_covered += 1
            population = city.get('population', 0)
            total_population += population
            
            # Check if already covered by existing PODs (for redundancy)
            already_covered = False
            if existing_pods:
                for existing_pod in existing_pods:
                    existing_lat = existing_pod.get('latitude', existing_pod.get('lat'))
                    existing_lon = existing_pod.get('longitude', existing_pod.get('lon'))
                    existing_radius = existing_pod.get('coverage_radius', 50.0)
                    
                    if existing_lat and existing_lon:
                        existing_distance = haversine_distance(
                            existing_lat, existing_lon, city_lat, city_lon
                        )
                        if existing_distance <= existing_radius:
                            already_covered = True
                            overlap_population += population
                            break
            
            # Calculate risk score
            risk = calculate_risk_score(city)
            
            # Apply scenario modifications if provided
            if scenario:
                risk = apply_scenario_risk_modification(risk, city, scenario)
            
            total_risk += risk * population  # Weight by population
            
            # Estimate vulnerable population
            vulnerability = calculate_vulnerability_score(city)
            vulnerable_population += int(population * vulnerability)
            
            # Calculate drive time
            drive_time = calculate_drive_time(pod_lat, pod_lon, city_lat, city_lon, use_api=False)
            drive_times.append(drive_time)
    
    avg_drive_time = sum(drive_times) / len(drive_times) if drive_times else 0.0
    max_drive_time = max(drive_times) if drive_times else 0.0
    
    # Calculate redundancy score (overlap is good for critical areas)
    redundancy_score = overlap_population / total_population if total_population > 0 else 0.0
    
    return {
        'points_covered': points_covered,
        'total_risk_covered': total_risk,
        'total_population_covered': total_population,
        'vulnerable_population_covered': vulnerable_population,
        'avg_drive_time': avg_drive_time,
        'max_drive_time': max_drive_time,
        'overlap_population': overlap_population,
        'redundancy_score': redundancy_score,
    }


def optimize_pod_locations(num_pods: int, max_drive_time: float = 60.0,
                          scenario: Optional[Dict] = None,
                          min_capacity: int = 1000,
                          enable_redundancy: bool = True) -> List[Dict]:
    """
    Enhanced greedy algorithm with multi-objective optimization to find optimal POD locations.
    
    Features:
    - Dynamic coverage radius based on population density
    - Capacity constraints
    - Multi-objective scoring (coverage, risk, accessibility, infrastructure, redundancy)
    - Vulnerable population prioritization
    - Iterative refinement
    
    Args:
        num_pods: Number of PODs to place
        max_drive_time: Maximum acceptable drive time in minutes
        scenario: Optional scenario dictionary for risk modifications
        min_capacity: Minimum daily capacity required for a POD
        enable_redundancy: Whether to prioritize redundancy for critical areas
    
    Returns:
        List of optimal POD locations with coverage statistics
    """
    demographic_data = load_demographic_data()
    
    if not demographic_data:
        return []
    
    # Phase 1: Calculate risk scores and initial city rankings
    city_scores = []
    for city in demographic_data:
        risk = calculate_risk_score(city)
        
        # Apply scenario modifications if provided
        if scenario:
            risk = apply_scenario_risk_modification(risk, city, scenario)
        
        # Enhanced initial score with vulnerability
        vulnerability = calculate_vulnerability_score(city)
        population = city.get('population', 0)
        
        # Weight by population, risk, and vulnerability
        score = population * risk * (1 + vulnerability * 0.3)
        
        city_scores.append({
            'city': city,
            'score': score,
            'risk': risk,
            'vulnerability': vulnerability,
        })
    
    city_scores.sort(key=lambda x: x['score'], reverse=True)
    
    selected_pods = []
    used_cities = set()
    
    # Phase 2: Greedy selection with enhanced scoring
    for iteration in range(num_pods):
        best_candidate = None
        best_coverage_score = -1
        
        # Evaluate top candidates (expand search if needed)
        candidate_pool_size = min(50, len(city_scores))
        candidates = [cs for cs in city_scores[:candidate_pool_size] 
                     if cs['city']['name'] not in used_cities]
        
        # If we're running low on candidates, expand search
        if len(candidates) < 10 and iteration < num_pods - 1:
            candidates = [cs for cs in city_scores 
                         if cs['city']['name'] not in used_cities]
        
        for candidate in candidates:
            city = candidate['city']
            city_lat = city.get('lat')
            city_lon = city.get('lon')
            
            if city_lat is None or city_lon is None:
                continue
            
            # Calculate dynamic radius for this location
            dynamic_radius = calculate_dynamic_radius(city, demographic_data)
            
            # Get existing PODs for redundancy calculation
            existing_pods = [
                {
                    'latitude': pod['city'].get('lat'),
                    'longitude': pod['city'].get('lon'),
                    'coverage_radius': pod.get('radius', dynamic_radius)
                }
                for pod in selected_pods
            ] if enable_redundancy else None
            
            # Calculate coverage for this location
            coverage = calculate_pod_coverage(
                city_lat, city_lon, dynamic_radius, demographic_data, 
                scenario, existing_pods
            )
            
            # Check constraints
            # 1. Max drive time constraint
            if coverage['max_drive_time'] > max_drive_time:
                continue
            
            # 2. Capacity constraint (estimate based on city size)
            # Estimate required capacity: assume 10% of population needs service per day
            required_capacity = int(coverage['total_population_covered'] * 0.1)
            
            # Estimate POD capacity (use default if not specified)
            estimated_capacity = estimate_pod_capacity(0, 0, 0)['daily_capacity']
            # For optimal PODs, estimate based on city size
            if city.get('population', 0) > 50000:
                estimated_capacity = 5000  # Large city POD
            elif city.get('population', 0) > 20000:
                estimated_capacity = 3000  # Medium city POD
            else:
                estimated_capacity = 1500  # Small city POD
            
            if estimated_capacity < min_capacity:
                continue
            
            # Calculate capacity utilization (prefer 70-90% utilization)
            capacity_utilization = min(1.0, required_capacity / estimated_capacity) if estimated_capacity > 0 else 0
            if capacity_utilization > 1.0:  # Over capacity
                continue
            
            # Calculate infrastructure score
            infrastructure_score = calculate_infrastructure_score(city, demographic_data)
            
            # Calculate accessibility score (inverse of drive time, normalized)
            accessibility_score = 1.0 - (coverage['avg_drive_time'] / max_drive_time) if max_drive_time > 0 else 0.5
            accessibility_score = max(0.0, min(1.0, accessibility_score))
            
            # Calculate redundancy score (higher is better for critical areas)
            redundancy_score = coverage.get('redundancy_score', 0.0)
            # For high-risk areas, redundancy is more important
            risk_weighted_redundancy = redundancy_score * candidate['risk']
            
            # Multi-objective scoring with weights
            population_covered = coverage['total_population_covered']
            risk_mitigation = coverage['total_risk_covered']
            vulnerable_covered = coverage.get('vulnerable_population_covered', 0)
            
            # Enhanced coverage score
            coverage_score = (
                (population_covered * 0.30) +  # Coverage weight
                (risk_mitigation * 0.25) +      # Risk mitigation weight
                (vulnerable_covered * 0.15) +   # Vulnerable population weight
                (accessibility_score * 1000 * 0.15) +  # Accessibility weight
                (infrastructure_score * 1000 * 0.10) +  # Infrastructure weight
                (risk_weighted_redundancy * 500 * 0.05)  # Redundancy weight (for critical areas)
            )
            
            # Bonus for good capacity utilization (70-90% is ideal)
            if 0.7 <= capacity_utilization <= 0.9:
                coverage_score *= 1.1  # 10% bonus for optimal capacity
            
            if coverage_score > best_coverage_score:
                best_coverage_score = coverage_score
                best_candidate = {
                    'city': city,
                    'coverage': coverage,
                    'coverage_score': coverage_score,
                    'radius': dynamic_radius,
                    'estimated_capacity': estimated_capacity,
                    'capacity_utilization': capacity_utilization,
                    'infrastructure_score': infrastructure_score,
                }
        
        if best_candidate:
            selected_pods.append(best_candidate)
            city_name = best_candidate['city']['name']
            used_cities.add(city_name)
            
            # Remove nearby candidates (within dynamic radius * 0.6 to prevent clustering)
            city_lat = best_candidate['city'].get('lat')
            city_lon = best_candidate['city'].get('lon')
            exclusion_radius = best_candidate['radius'] * 0.6
            
            for cs in city_scores:
                other_city = cs['city']
                other_lat = other_city.get('lat')
                other_lon = other_city.get('lon')
                
                if other_lat and other_lon:
                    distance = haversine_distance(city_lat, city_lon, other_lat, other_lon)
                    if distance <= exclusion_radius:
                        used_cities.add(other_city['name'])
    
    # Phase 3: Iterative refinement (local optimization)
    # Try swapping PODs to see if we can improve coverage
    if len(selected_pods) > 1:
        improved = True
        refinement_iterations = 0
        max_refinements = 3
        
        while improved and refinement_iterations < max_refinements:
            improved = False
            refinement_iterations += 1
            
            for i in range(len(selected_pods)):
                current_pod = selected_pods[i]
                current_score = current_pod['coverage_score']
                
                # Try nearby alternatives
                city = current_pod['city']
                city_lat = city.get('lat')
                city_lon = city.get('lon')
                
                # Find nearby cities not already used
                nearby_alternatives = []
                for cs in city_scores:
                    alt_city = cs['city']
                    alt_lat = alt_city.get('lat')
                    alt_lon = alt_city.get('lon')
                    
                    if alt_lat and alt_lon and alt_city['name'] not in used_cities:
                        distance = haversine_distance(city_lat, city_lon, alt_lat, alt_lon)
                        if 10 <= distance <= 50:  # Within 10-50km
                            nearby_alternatives.append(cs)
                
                # Evaluate alternatives
                for alt_candidate in nearby_alternatives[:5]:  # Check top 5 alternatives
                    alt_city = alt_candidate['city']
                    alt_lat = alt_city.get('lat')
                    alt_lon = alt_city.get('lon')
                    
                    if alt_lat is None or alt_lon is None:
                        continue
                    
                    # Recalculate with alternative
                    alt_radius = calculate_dynamic_radius(alt_city, demographic_data)
                    other_pods = [
                        {
                            'latitude': pod['city'].get('lat'),
                            'longitude': pod['city'].get('lon'),
                            'coverage_radius': pod.get('radius', alt_radius)
                        }
                        for j, pod in enumerate(selected_pods) if j != i
                    ]
                    
                    alt_coverage = calculate_pod_coverage(
                        alt_lat, alt_lon, alt_radius, demographic_data, scenario, other_pods
                    )
                    
                    if alt_coverage['max_drive_time'] > max_drive_time:
                        continue
                    
                    # Recalculate score (simplified for refinement)
                    alt_score = (
                        alt_coverage['total_population_covered'] * 0.4 +
                        alt_coverage['total_risk_covered'] * 0.3 +
                        (1.0 - alt_coverage['avg_drive_time'] / max_drive_time) * 1000 * 0.3
                    )
                    
                    if alt_score > current_score * 1.05:  # 5% improvement threshold
                        # Swap to alternative
                        selected_pods[i] = {
                            'city': alt_city,
                            'coverage': alt_coverage,
                            'coverage_score': alt_score,
                            'radius': alt_radius,
                            'estimated_capacity': current_pod['estimated_capacity'],
                            'capacity_utilization': current_pod['capacity_utilization'],
                            'infrastructure_score': calculate_infrastructure_score(alt_city, demographic_data),
                        }
                        used_cities.remove(city['name'])
                        used_cities.add(alt_city['name'])
                        improved = True
                        break
                
                if improved:
                    break
    
    # Format results
    results = []
    for i, pod_data in enumerate(selected_pods, 1):
        city = pod_data['city']
        coverage = pod_data['coverage']
        
        results.append({
            'name': f'Optimal POD {i} - {city["name"]}',
            'latitude': round(city['lat'], 6),
            'longitude': round(city['lon'], 6),
            'coverage_radius': round(pod_data['radius'], 1),
            'points_covered': coverage['points_covered'],
            'total_risk_covered': coverage['total_risk_covered'],
            'total_population_covered': coverage['total_population_covered'],
            'vulnerable_population_covered': coverage.get('vulnerable_population_covered', 0),
            'avg_drive_time': coverage['avg_drive_time'],
            'max_drive_time': coverage['max_drive_time'],
            'redundancy_score': coverage.get('redundancy_score', 0.0),
            'infrastructure_score': pod_data.get('infrastructure_score', 0.0),
            'estimated_capacity': pod_data.get('estimated_capacity', 0),
            'capacity_utilization': pod_data.get('capacity_utilization', 0.0),
            'status': 'proposed',
        })
    
    return results


def analyze_coverage_gaps(selected_pods: List[Dict], demographic_data: List[Dict],
                          scenario: Optional[Dict] = None, 
                          min_coverage_radius: float = 50.0) -> Dict:
    """
    Analyze coverage gaps after POD placement.
    
    Args:
        selected_pods: List of selected POD locations
        demographic_data: All demographic data
        scenario: Optional scenario for risk modifications
        min_coverage_radius: Minimum coverage radius to check
    
    Returns:
        Dictionary with gap analysis results
    """
    covered_cities = set()
    uncovered_population = 0
    uncovered_risk = 0.0
    gap_areas = []
    
    # Check which cities are covered
    for pod in selected_pods:
        pod_lat = pod.get('latitude', pod.get('city', {}).get('lat'))
        pod_lon = pod.get('longitude', pod.get('city', {}).get('lon'))
        pod_radius = pod.get('coverage_radius', min_coverage_radius)
        
        if pod_lat is None or pod_lon is None:
            continue
        
        for city in demographic_data:
            city_lat = city.get('lat')
            city_lon = city.get('lon')
            city_name = city.get('name')
            
            if city_lat is None or city_lon is None:
                continue
            
            distance = haversine_distance(pod_lat, pod_lon, city_lat, city_lon)
            if distance <= pod_radius:
                covered_cities.add(city_name)
    
    # Find uncovered areas
    for city in demographic_data:
        city_name = city.get('name')
        if city_name not in covered_cities:
            population = city.get('population', 0)
            uncovered_population += population
            
            risk = calculate_risk_score(city)
            if scenario:
                risk = apply_scenario_risk_modification(risk, city, scenario)
            
            uncovered_risk += risk * population
            
            gap_areas.append({
                'name': city_name,
                'lat': city.get('lat'),
                'lon': city.get('lon'),
                'population': population,
                'risk_score': risk,
                'priority': population * risk,  # Priority for gap filling
            })
    
    # Sort gaps by priority
    gap_areas.sort(key=lambda x: x['priority'], reverse=True)
    
    total_population = sum(c.get('population', 0) for c in demographic_data)
    coverage_percentage = ((total_population - uncovered_population) / total_population * 100) if total_population > 0 else 0
    
    return {
        'total_population': total_population,
        'covered_population': total_population - uncovered_population,
        'uncovered_population': uncovered_population,
        'coverage_percentage': round(coverage_percentage, 2),
        'uncovered_risk': uncovered_risk,
        'gap_count': len(gap_areas),
        'critical_gaps': gap_areas[:10],  # Top 10 critical gaps
    }

