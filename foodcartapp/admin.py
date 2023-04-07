from urllib.parse import unquote

from django.contrib import admin
from django.shortcuts import redirect
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme

from .models import Order
from .models import OrderProduct
from .models import Product
from .models import ProductCategory
from .models import Restaurant
from .models import RestaurantMenuItem
from .utils import fetch_coordinates, get_eligible_restaurants, calculate_distance


class RestaurantMenuItemInline(admin.TabularInline):
    model = RestaurantMenuItem
    extra = 0


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    search_fields = [
        'name',
        'address',
        'contact_phone',

    ]
    list_display = [
        'name',
        'address',
        'contact_phone',
        'latitude',
        'longitude',
    ]
    inlines = [
        RestaurantMenuItemInline,
    ]

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            if not (obj.latitude and obj.longitude):
                longitude, latitude = fetch_coordinates(obj.address)
                obj.latitude = latitude
                obj.longitude = longitude
        super().save_model(request, obj, form, change)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'get_image_list_preview',
        'name',
        'category',
        'price',
    ]
    list_display_links = [
        'name',
    ]
    list_filter = [
        'category',
    ]
    search_fields = [
        # FIXME SQLite can not convert letter case for cyrillic words properly, so search will be buggy.
        # Migration to PostgreSQL is necessary
        'name',
        'category__name',
    ]

    inlines = [
        RestaurantMenuItemInline,
    ]
    fieldsets = (
        ('Общее', {
            'fields': [
                'name',
                'category',
                'image',
                'get_image_preview',
                'price',
            ]
        }),
        ('Подробно', {
            'fields': [
                'special_status',
                'description',
            ],
            'classes': [
                'wide'
            ],
        }),
    )

    readonly_fields = [
        'get_image_preview',
    ]

    class Media:
        css = {
            "all": (
                static("admin/foodcartapp.css")
            )
        }

    def get_image_preview(self, obj):
        if not obj.image:
            return 'выберите картинку'
        return format_html('<img src="{url}" style="max-height: 200px;"/>', url=obj.image.url)

    get_image_preview.short_description = 'превью'

    def get_image_list_preview(self, obj):
        if not obj.image or not obj.id:
            return 'нет картинки'
        edit_url = reverse('admin:foodcartapp_product_change', args=(obj.id,))
        return format_html('<a href="{edit_url}"><img src="{src}" style="max-height: 50px;"/></a>', edit_url=edit_url,
                           src=obj.image.url)

    get_image_list_preview.short_description = 'превью'


@admin.register(ProductCategory)
class ProductAdmin(admin.ModelAdmin):
    pass


class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [
        OrderProductInline,
    ]
    list_display = (
        'id',
        'status',
        'payment_method',
        'total_cost_annotation',
        'order_date',
        'call_date',
        'delivery_date',
        'firstname',
        'lastname',
        'phonenumber',
        'assigned_restaurant',
        'address',
    )
    search_fields = (
        'id',
        'firstname',
        'lastname',
        'phonenumber',
        'address',
    )
    change_form_template = 'admin/order_change_form.html'

    def total_cost_annotation(self, obj):
        return obj.total_cost

    total_cost_annotation.short_description = 'Сумма заказа'

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        fields = [field for field in fields if field not in ['latitude', 'longitude']]
        return fields

    def response_change(self, request, obj):
        response = super().response_change(request, obj)
        next_url = request.GET.get('next')
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None,
                                                        require_https=request.is_secure()):
            return redirect(next_url)
        return response

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        obj = self.get_object(request, unquote(object_id)) if object_id else None

        if obj:
            restaurants_info = []

            eligible_restaurants = get_eligible_restaurants(obj)
            for restaurant in Restaurant.objects.all():
                distance = None
                if obj.latitude and obj.longitude and restaurant.latitude and restaurant.longitude:
                    distance = calculate_distance(obj.latitude, obj.longitude, restaurant.latitude,
                                                  restaurant.longitude)

                can_prepare = restaurant in eligible_restaurants
                restaurants_info.append({
                    'restaurant': restaurant,
                    'distance': distance,
                    'can_prepare': can_prepare,
                })

            extra_context['restaurants_info'] = restaurants_info

        return super().changeform_view(request, object_id, form_url, extra_context)
