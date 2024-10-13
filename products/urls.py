from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='home'),  # Root URL redirects to product list
    path('products/bulk-insert/', views.bulk_insert_products, name='bulk_insert_products'),
    path('products/', views.product_list, name='product_list'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
]
