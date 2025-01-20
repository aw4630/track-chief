from django.db import models

# backend/api/models.py


class TrackUsage(models.Model):
    usage_id = models.AutoField(primary_key=True)
    train_number = models.CharField(max_length=20, null=False)
    route_short_name = models.CharField(max_length=20, null=False)
    departure_time = models.DateTimeField(null=False) 
    track = models.CharField(max_length=20, null=False)

    class Meta:
        db_table = 'track_usage'
        unique_together = ('train_number', 'departure_time')  # Prevent duplicate entries (same train # and timestamp)
        ordering = ['-departure_time']  # Order by departure time descending 

    def __str__(self):
        return f"{self.train_number} - {self.route_short_name} - {self.departure_time} - {self.track}"
