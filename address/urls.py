from django.urls import path
from .api import CityListAPIView

urlpatterns = [
    path('api/cities/', CityListAPIView.as_view(), name='cities'),
]
