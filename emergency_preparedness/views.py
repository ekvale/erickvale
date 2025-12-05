from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import POD, Scenario
from .serializers import (
    PODSerializer, ScenarioSerializer, DemographicDataSerializer,
    RiskDataSerializer, DriveTimeSerializer
)
from .utils import (
    load_demographic_data, calculate_risk_score, apply_scenario_risk_modification,
    calculate_drive_time, optimize_pod_locations, calculate_pod_coverage,
    analyze_coverage_gaps
)


def scenario_to_dict(scenario_obj):
    """Convert Scenario model instance to dictionary format."""
    return {
        'type': scenario_obj.type,
        'severity': scenario_obj.severity,
        'affected_areas': scenario_obj.affected_areas or [],
    }


class PODViewSet(viewsets.ModelViewSet):
    """ViewSet for POD CRUD operations."""
    
    queryset = POD.objects.all()
    serializer_class = PODSerializer
    
    @action(detail=False, methods=['get'])
    def optimal(self, request):
        """
        Generate optimal POD locations with enhanced multi-objective optimization.
        
        Query parameters:
        - num_pods: Number of PODs to generate (default: 5)
        - max_drive_time: Maximum drive time in minutes (default: 60)
        - scenario_id: Optional scenario ID for scenario-specific optimization
        - min_capacity: Minimum daily capacity required (default: 1000)
        - enable_redundancy: Enable redundancy planning (default: true)
        - analyze_gaps: Include coverage gap analysis (default: false)
        """
        num_pods = int(request.query_params.get('num_pods', 5))
        max_drive_time = float(request.query_params.get('max_drive_time', 60.0))
        scenario_id = request.query_params.get('scenario_id', None)
        min_capacity = int(request.query_params.get('min_capacity', 1000))
        enable_redundancy = request.query_params.get('enable_redundancy', 'true').lower() == 'true'
        analyze_gaps = request.query_params.get('analyze_gaps', 'false').lower() == 'true'
        
        scenario = None
        if scenario_id:
            try:
                scenario_obj = Scenario.objects.get(id=scenario_id)
                scenario = scenario_to_dict(scenario_obj)
            except Scenario.DoesNotExist:
                pass
        
        optimal_pods = optimize_pod_locations(
            num_pods, max_drive_time, scenario, min_capacity, enable_redundancy
        )
        
        response_data = {
            'pods': optimal_pods,
            'summary': {
                'total_pods': len(optimal_pods),
                'total_population_covered': sum(p.get('total_population_covered', 0) for p in optimal_pods),
                'total_risk_covered': sum(p.get('total_risk_covered', 0) for p in optimal_pods),
                'avg_infrastructure_score': sum(p.get('infrastructure_score', 0) for p in optimal_pods) / len(optimal_pods) if optimal_pods else 0,
            }
        }
        
        # Add gap analysis if requested
        if analyze_gaps:
            demographic_data = load_demographic_data()
            gap_analysis = analyze_coverage_gaps(optimal_pods, demographic_data, scenario)
            response_data['gap_analysis'] = gap_analysis
        
        return Response(response_data)
    
    def perform_create(self, serializer):
        """Override create to calculate coverage after saving."""
        pod = serializer.save()
        self._update_pod_coverage(pod)
    
    def perform_update(self, serializer):
        """Override update to recalculate coverage after saving."""
        pod = serializer.save()
        self._update_pod_coverage(pod)
    
    def _update_pod_coverage(self, pod):
        """Calculate and update POD coverage statistics."""
        demographic_data = load_demographic_data()
        scenario = None  # Could be enhanced to use active scenario
        
        coverage = calculate_pod_coverage(
            float(pod.latitude),
            float(pod.longitude),
            pod.coverage_radius,
            demographic_data,
            scenario
        )
        
        pod.points_covered = coverage['points_covered']
        pod.total_risk_covered = coverage['total_risk_covered']
        pod.total_population_covered = coverage['total_population_covered']
        pod.avg_drive_time = coverage['avg_drive_time']
        pod.max_drive_time = coverage['max_drive_time']
        pod.save(update_fields=[
            'points_covered', 'total_risk_covered', 'total_population_covered',
            'avg_drive_time', 'max_drive_time'
        ])


class ScenarioViewSet(viewsets.ModelViewSet):
    """ViewSet for Scenario CRUD operations."""
    
    queryset = Scenario.objects.all()
    serializer_class = ScenarioSerializer
    
    @action(detail=True, methods=['get'])
    def risk_data(self, request, pk=None):
        """
        Get scenario-modified risk data.
        
        Returns demographic data with risk scores modified by the scenario.
        """
        scenario = self.get_object()
        demographic_data = load_demographic_data()
        scenario_dict = scenario_to_dict(scenario)
        
        risk_data = []
        for city in demographic_data:
            base_risk = calculate_risk_score(city)
            modified_risk = apply_scenario_risk_modification(base_risk, city, scenario_dict)
            
            risk_data.append({
                'name': city.get('name', ''),
                'lat': city.get('lat', 0),
                'lon': city.get('lon', 0),
                'population': city.get('population', 0),
                'risk_score': modified_risk,
                'county': city.get('county', ''),
            })
        
        serializer = RiskDataSerializer(risk_data, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def analyze(self, request, pk=None):
        """
        Analyze scenario coverage.
        
        Returns coverage statistics for PODs associated with this scenario.
        """
        scenario = self.get_object()
        associated_pods = scenario.pods.all()
        scenario_dict = scenario_to_dict(scenario)
        
        demographic_data = load_demographic_data()
        
        total_points_covered = 0
        total_risk_covered = 0.0
        total_population_covered = 0
        all_drive_times = []
        
        covered_cities = set()
        
        for pod in associated_pods:
            coverage = calculate_pod_coverage(
                float(pod.latitude),
                float(pod.longitude),
                pod.coverage_radius,
                demographic_data,
                scenario_dict
            )
            
            total_points_covered += coverage['points_covered']
            total_risk_covered += coverage['total_risk_covered']
            total_population_covered += coverage['total_population_covered']
            
            if coverage['avg_drive_time'] > 0:
                all_drive_times.append(coverage['avg_drive_time'])
            if coverage['max_drive_time'] > 0:
                all_drive_times.append(coverage['max_drive_time'])
            
            # Track covered cities
            for city in demographic_data:
                city_lat = city.get('lat')
                city_lon = city.get('lon')
                if city_lat and city_lon:
                    from .utils import haversine_distance
                    distance = haversine_distance(
                        float(pod.latitude), float(pod.longitude),
                        city_lat, city_lon
                    )
                    if distance <= pod.coverage_radius:
                        covered_cities.add(city.get('name', ''))
        
        total_cities = len(demographic_data)
        coverage_percentage = (len(covered_cities) / total_cities * 100) if total_cities > 0 else 0
        
        avg_drive_time = sum(all_drive_times) / len(all_drive_times) if all_drive_times else 0.0
        max_drive_time = max(all_drive_times) if all_drive_times else 0.0
        
        analysis = {
            'scenario_id': scenario.id,
            'scenario_name': scenario.name,
            'num_pods': associated_pods.count(),
            'total_points_covered': total_points_covered,
            'total_risk_covered': total_risk_covered,
            'total_population_covered': total_population_covered,
            'coverage_percentage': round(coverage_percentage, 2),
            'avg_drive_time': round(avg_drive_time, 2),
            'max_drive_time': round(max_drive_time, 2),
            'cities_covered': len(covered_cities),
            'total_cities': total_cities,
        }
        
        return Response(analysis)


class DemographicDataView(APIView):
    """API view for demographic data."""
    
    def get(self, request):
        """Get demographic data."""
        data = load_demographic_data()
        serializer = DemographicDataSerializer(data, many=True)
        return Response(serializer.data)


class RiskDataView(APIView):
    """API view for risk data."""
    
    def get(self, request):
        """
        Get base risk data or scenario-specific risk data.
        
        Query parameters:
        - scenario_id: Optional scenario ID for scenario-specific risk calculations
        """
        scenario_id = request.query_params.get('scenario_id', None)
        demographic_data = load_demographic_data()
        
        scenario = None
        if scenario_id:
            try:
                scenario_obj = Scenario.objects.get(id=scenario_id)
                scenario = scenario_to_dict(scenario_obj)
            except Scenario.DoesNotExist:
                pass
        
        risk_data = []
        for city in demographic_data:
            base_risk = calculate_risk_score(city)
            
            if scenario:
                modified_risk = apply_scenario_risk_modification(base_risk, city, scenario)
            else:
                modified_risk = base_risk
            
            risk_data.append({
                'name': city.get('name', ''),
                'lat': city.get('lat', 0),
                'lon': city.get('lon', 0),
                'population': city.get('population', 0),
                'risk_score': modified_risk,
                'county': city.get('county', ''),
            })
        
        serializer = RiskDataSerializer(risk_data, many=True)
        return Response(serializer.data)


class DriveTimeView(APIView):
    """API view for drive time calculation."""
    
    def post(self, request):
        """Calculate drive time between two points."""
        serializer = DriveTimeSerializer(data=request.data)
        if serializer.is_valid():
            lat1 = serializer.validated_data['lat1']
            lon1 = serializer.validated_data['lon1']
            lat2 = serializer.validated_data['lat2']
            lon2 = serializer.validated_data['lon2']
            
            drive_time = calculate_drive_time(lat1, lon1, lat2, lon2)
            
            return Response({
                'lat1': lat1,
                'lon1': lon1,
                'lat2': lat2,
                'lon2': lon2,
                'drive_time': round(drive_time, 2),
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@ensure_csrf_cookie
def index(request):
    """Main view for the emergency preparedness app."""
    return render(request, 'emergency_preparedness/index.html')
