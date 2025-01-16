from django.contrib import admin
from . import views
from django.urls import path


app_name = "products"
urlpatterns = [
    path("", views.get_products, name="get_products"),
    
]
