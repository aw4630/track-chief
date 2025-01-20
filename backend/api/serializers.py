# backend/serializers.py
from rest_framework import serializers
from .models import TrackUsage

class TrackUsageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrackUsage
        fields = ['usage_id', 'train_number', 'route_short_name', 'departure_time', 'track']
        read_only_fields = ['usage_id']  # auto-generated usage id for each entry recorded