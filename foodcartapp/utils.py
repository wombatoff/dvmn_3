from math import sin, cos, sqrt, atan2, radians

import requests
from django.conf import settings

from .models import Order, Restaurant, RestaurantMenuItem


def get_eligible_restaurants(order: Order):
    eligible_restaurants = set()

    for product in order.products.all():
        restaurants_with_product = (
            RestaurantMenuItem.objects
            .filter(product=product, availability=True)
            .select_related('restaurant')
            .values_list('restaurant', flat=True)
        )
        restaurant_objects = Restaurant.objects.filter(id__in=restaurants_with_product)

        if not eligible_restaurants:
            eligible_restaurants.update(restaurant_objects)
        else:
            eligible_restaurants.intersection_update(restaurant_objects)

        if not eligible_restaurants:
            break

    return eligible_restaurants


def fetch_coordinates(address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": settings.YANDEX_API_KEY,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


def calculate_distance(lat1, lon1, lat2, lon2):
    earth_radius_in_km = 6371

    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))
    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    sin_half_dist_sqr = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    central_angle = 2 * atan2(sqrt(sin_half_dist_sqr), sqrt(1 - sin_half_dist_sqr))

    return earth_radius_in_km * central_angle
