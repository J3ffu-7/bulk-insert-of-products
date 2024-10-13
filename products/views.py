# Create an API view for bulk inserting
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from .models import Product, ProductVariant
import json
from django.shortcuts import render

# Bulk insert products 
@csrf_exempt
def bulk_insert_products(request):
    if request.method == 'GET':
        # Render the bulk insert form template
        return render(request, 'bulk_insert.html')

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            products_data = data.get('products', [])
            product_variants = []

            with transaction.atomic():
                for p in products_data:
                    if p.get('delete', False):
                        # If the product is marked for deletion, delete the product by its name (or any identifier)
                        try:
                            product = Product.objects.get(name=p['name'])
                            product.delete()  # This will delete the product and its variants (due to cascade)
                        except Product.DoesNotExist:
                            continue
                    else:
                        # Step 1: Create or update the product
                        product, created = Product.objects.get_or_create(name=p['name'], defaults={'image': p['image']})
                        if not created:
                            product.image = p['image']
                            product.save()

                        # Step 2: Handle variants
                        for variant_data in p.get('variants', []):
                            if variant_data.get('delete', False):
                                # Delete the variant if marked for deletion
                                try:
                                    variant = ProductVariant.objects.get(product=product, sku=variant_data['sku'])
                                    variant.delete()
                                except ProductVariant.DoesNotExist:
                                    continue
                            else:
                                # Create or update the variant
                                variant, created = ProductVariant.objects.get_or_create(
                                    product=product,
                                    sku=variant_data['sku'],
                                    defaults={
                                        'name': variant_data['name'],
                                        'price': variant_data['price'],
                                        'details': variant_data.get('details', '')
                                    }
                                )
                                if not created:
                                    variant.name = variant_data['name']
                                    variant.price = variant_data['price']
                                    variant.details = variant_data.get('details', '')
                                    variant.save()

            return JsonResponse({"message": "Products and variants inserted/deleted successfully!"}, status=201)
        
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

# List all products with their variants
def product_list(request):
    products = Product.objects.prefetch_related('variants').all()  # Optimize with prefetch_related
    data = []

    for product in products:
        variants = product.variants.all()  # Correct way to access related variants
        data.append({
            'id': product.id,
            'name': product.name,
            'image': product.image if product.image else '',
            'variants': [
                {
                    'id': variant.id,
                    'sku': variant.sku,
                    'name': variant.name,
                    'price': variant.price,
                    'details': variant.details
                } for variant in variants
            ]
        })
    
    # Render the template with the data
    return render(request, 'product_list.html', {'products': data})


# Retrieve, update, or delete a single product
@csrf_exempt
def product_detail(request, pk):
    try:
        product = Product.objects.get(pk=pk)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)

    if request.method == 'GET':
        # Get product details with variants
        variants = product.variants.all()

        # Render the HTML template with product and variants
        return render(request, 'product_detail.html', {
            'product': product,
            'variants': variants,
        })

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)

            if data.get('delete', False):
                # If delete flag is set, delete the product
                product.delete()
                return JsonResponse({"message": "Product deleted successfully!"})

            # Update product fields
            product.name = data['name']
            product.image = data['image']
            product.save()

            # Handle variants update and deletion
            variants_data = data.get('variants', [])
            for variant_data in variants_data:
                # Handle variant deletion
                if variant_data.get('delete', False):
                    try:
                        variant = ProductVariant.objects.get(pk=variant_data['id'])
                        variant.delete()
                    except ProductVariant.DoesNotExist:
                        continue

                # Handle variant update or creation
                else:
                    if 'id' in variant_data and variant_data['id']:
                        # Update the existing variant
                        try:
                            variant = ProductVariant.objects.get(pk=variant_data['id'])
                            variant.name = variant_data['name']
                            variant.sku = variant_data['sku']
                            variant.price = variant_data['price']
                            variant.details = variant_data.get('details', '')
                            variant.save()
                        except ProductVariant.DoesNotExist:
                            continue
                    else:
                        # Create new variant (no ID present)
                        ProductVariant.objects.create(
                            product=product,
                            sku=variant_data['sku'],
                            name=variant_data['name'],
                            price=variant_data['price'],
                            details=variant_data.get('details', '')
                        )

            return JsonResponse({"message": "Product and variants updated successfully!"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    elif request.method == 'DELETE':
        # Handle product deletion
        product.delete()
        return JsonResponse({"message": "Product deleted successfully!"}, status=204)


    return JsonResponse({"error": "Invalid request method"}, status=405)
