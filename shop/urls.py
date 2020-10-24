from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.all_product_catogories, name='all_product_catogories'),
    path('<slug:c_slug>/', views.all_product_catogories, name='products_by_category'),
    path('<slug:c_slug>/<slug:product_slug>/', views.product_category_detail, name='product_category_detail'),
]
