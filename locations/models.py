import requests
from geopy import distance
from django.conf import settings
from django.db import models
from django.utils import timezone


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


class LocationManager(models.Manager):
    
    def get_for_addresses(self, addresses: set):
        '''Get locations from DB; fetch and save any address that is missing'''

        locations_from_db = {
            location.address: location for location 
            in self.filter(address__in=addresses)
        }

        new_addresses = addresses.difference(locations_from_db.keys())

        for address in new_addresses:
            coords = fetch_coordinates(settings.GEO_API_KEY, address)
            lon, lat = coords if coords else (None, None)

            location = self.create(
                address=address,
                lon=lon,
                lat=lat
            )

            locations_from_db[address] = location

        return locations_from_db
        

class Location(models.Model):
    address = models.CharField(
        'Адрес',
        unique=True,
        max_length=200,
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

    objects = LocationManager()

    def distance_to(self, other: 'Location'):
        if (self.lat and self.lon and other.lat and other.lon) is None:
            return
        
        return distance.distance(
            (self.lat, self.lon), 
            (other.lat, other.lon)
        ).km

    def __str__(self) -> str:
        return f'{self.address} ({self.lat}, {self.lon})'