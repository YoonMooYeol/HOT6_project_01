from django.core.cache import cache
from django.shortcuts import render
from .models import Product
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import ProductSerializer

# Create your views here.
@api_view(['GET'])
def get_products(request):
    cache_key = "products"
    
    if not cache.get(cache_key):
        print("Cache miss")
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        json_data = serializer.data
        cache.set(cache_key, json_data, 180)
        
    json_response = cache.get("products")
    return Response(json_response)\
        
        
