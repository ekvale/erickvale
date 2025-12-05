from rest_framework import serializers
from decimal import Decimal, ROUND_HALF_UP
from .models import POD, Scenario, ScenarioPOD
from .utils import constrain_to_minnesota, calculate_pod_coverage, load_demographic_data


class PODSerializer(serializers.ModelSerializer):
    """Serializer for POD model."""
    
    class Meta:
        model = POD
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'points_covered', 
                          'total_risk_covered', 'total_population_covered',
                          'avg_drive_time', 'max_drive_time')
    
    def validate_latitude(self, value):
        """Validate and constrain latitude to Minnesota bounds."""
        lat, _ = constrain_to_minnesota(float(value), -94.0)
        # Round to 6 decimal places
        lat = round(lat, 6)
        return Decimal(str(lat))
    
    def validate_longitude(self, value):
        """Validate and constrain longitude to Minnesota bounds."""
        _, lon = constrain_to_minnesota(46.0, float(value))
        # Round to 6 decimal places
        lon = round(lon, 6)
        return Decimal(str(lon))


class ScenarioPODSerializer(serializers.ModelSerializer):
    """Serializer for ScenarioPOD relationship."""
    
    pod = PODSerializer(read_only=True)
    pod_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ScenarioPOD
        fields = ('id', 'pod', 'pod_id', 'created_at')
        read_only_fields = ('created_at',)


class ScenarioSerializer(serializers.ModelSerializer):
    """Serializer for Scenario model."""
    
    pods = PODSerializer(many=True, read_only=True)
    pod_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Scenario
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
    
    def create(self, validated_data):
        """Create scenario and associate PODs."""
        pod_ids = validated_data.pop('pod_ids', [])
        scenario = Scenario.objects.create(**validated_data)
        
        for pod_id in pod_ids:
            try:
                pod = POD.objects.get(id=pod_id)
                ScenarioPOD.objects.create(scenario=scenario, pod=pod)
            except POD.DoesNotExist:
                pass
        
        return scenario
    
    def update(self, instance, validated_data):
        """Update scenario and POD associations."""
        pod_ids = validated_data.pop('pod_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if pod_ids is not None:
            # Clear existing associations
            ScenarioPOD.objects.filter(scenario=instance).delete()
            # Create new associations
            for pod_id in pod_ids:
                try:
                    pod = POD.objects.get(id=pod_id)
                    ScenarioPOD.objects.create(scenario=instance, pod=pod)
                except POD.DoesNotExist:
                    pass
        
        return instance


class DemographicDataSerializer(serializers.Serializer):
    """Serializer for demographic data."""
    name = serializers.CharField()
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    population = serializers.IntegerField()
    county = serializers.CharField()


class RiskDataSerializer(serializers.Serializer):
    """Serializer for risk data."""
    name = serializers.CharField()
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    population = serializers.IntegerField()
    risk_score = serializers.FloatField()
    county = serializers.CharField()


class DriveTimeSerializer(serializers.Serializer):
    """Serializer for drive time calculation."""
    lat1 = serializers.FloatField()
    lon1 = serializers.FloatField()
    lat2 = serializers.FloatField()
    lon2 = serializers.FloatField()
    drive_time = serializers.FloatField(read_only=True)

