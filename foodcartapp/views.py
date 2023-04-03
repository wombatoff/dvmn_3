import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from django.views.decorators.csrf import csrf_exempt

from .models import Product, Order, OrderProduct


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@csrf_exempt
def register_order(request):
    if request.method == 'POST':
        try:
            order_request = json.loads(request.body.decode())
        except ValueError:
            return JsonResponse({
                'error': 'Невалидный JSON',
            })

        order = Order.objects.create(
            customer_firstname=order_request['firstname'],
            customer_lastname=order_request['lastname'],
            customer_phone=order_request['phonenumber'],
            customer_address=order_request['address'],
        )

        for product in order_request['products']:
            item = OrderProduct.objects.create(
                order=order,
                product=get_object_or_404(Product, pk=product['product']),
                quantity=product['quantity']
            )

        return JsonResponse({
            'message': 'Order registered successfully',
            'order': order_request,
        })

    return JsonResponse({'error': 'Invalid request method'})
