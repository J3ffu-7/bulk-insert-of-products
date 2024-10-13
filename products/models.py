from django.db import models

# Define the Product and ProductVariant models

class Product(models.Model):
    name = models.CharField(max_length=255)
    image = models.CharField(max_length=255)

class ProductVariant(models.Model):
    sku = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    details = models.TextField(null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
