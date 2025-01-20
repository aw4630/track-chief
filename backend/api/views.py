# backend/api/views.py

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from .models import TrackUsage
from .serializers import TrackUsageSerializer

class TrackUsageViewSet(viewsets.ModelViewSet):
    queryset = TrackUsage.objects.all()
    serializer_class = TrackUsageSerializer

    @action(detail=False, methods=['get'])
    def latest(self):
        # Get the latest track assignments (last 10 assignments)
        latest = self.queryset.order_by('-departure_time')[:10]
        serializer = self.get_serializer(latest, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def today(self):
        # Get all track assignments for today 
        today = timezone.now().date()
        today_records = self.queryset.filter(
            departure_time__date=today
        ).order_by('departure_time')
        serializer = self.get_serializer(today_records, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_route(self, request):
        # Get track assignments filtered by route_short_name (ex: 'NEC')
        route = request.query_params.get('route', None)
        if route:
            records = self.queryset.filter(
                route_short_name=route
            ).order_by('-departure_time')
            serializer = self.get_serializer(records, many=True)
            return Response(serializer.data)
        return Response({'error': 'route parameter is required'}, status=400)