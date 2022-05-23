from django.db import models
from django.utils import timezone




#not migrated
class Location(models.Model):
    address = models.CharField(
        'Адрес',
        unique=True,
        max_length=200,
        blank=False,
        db_index=True
    )

    lat = models.FloatField(
        'Положение по широте',
        null=True
    )

    lon = models.FloatField(
        'Положение по долготе',
        null=True
    )

    fetched_on = models.DateTimeField(
        'Дата запроса к геокодеру',
        default=timezone.now
    )