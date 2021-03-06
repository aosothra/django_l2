from django import forms
from django.contrib import admin
from django.shortcuts import reverse
from django.templatetags.static import static
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.html import format_html
from django.http import HttpResponseRedirect

from .models import Order, OrderItem, Product
from .models import ProductCategory
from .models import Restaurant
from .models import RestaurantMenuItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem


class OrderAdminForm(forms.ModelForm):    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make sure to only list restaurants with matching avaliable products
        order_items = [item.product.id for item in self.instance.items.all()]
        restaurants_with_items = RestaurantMenuItem.objects.get_restaurants_with_items()

        avaliable_restaurants = [
            restaurant.id for restaurant, items in restaurants_with_items.items()
            if set(items).issuperset(order_items)
        ]

        self.fields['assigned_restaurant'].queryset = Restaurant.objects.filter(id__in=avaliable_restaurants)

        
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderAdminForm

    fields = (
        ('phonenumber', 'firstname', 'lastname'),
        ('address'),
        ('created_on', 'confirmed_on', 'fulfilled_on'),
        ('status', 'payment_method', 'assigned_restaurant'),
        ('note'),
    )
    readonly_fields = [
        'created_on',
    ]    
    inlines = [
        OrderItemInline
    ]

    def response_post_save_change(self, request, obj):
        # Redirect back if request comes from manager view

        generic_response = super().response_post_save_change(request, obj)
        redirect_url = request.GET.get('next')
        return (
            HttpResponseRedirect(redirect_url)
            if redirect_url and url_has_allowed_host_and_scheme(redirect_url, None)
            else generic_response
        )

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
    ]
    inlines = [
        RestaurantMenuItemInline
    ]


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
        RestaurantMenuItemInline
    ]
    fieldsets = (
        ('??????????', {
            'fields': [
                'name',
                'category',
                'image',
                'get_image_preview',
                'price',
            ]
        }),
        ('????????????????', {
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
            return '???????????????? ????????????????'
        return format_html('<img src="{url}" style="max-height: 200px;"/>', url=obj.image.url)
    get_image_preview.short_description = '????????????'

    def get_image_list_preview(self, obj):
        if not obj.image or not obj.id:
            return '?????? ????????????????'
        edit_url = reverse('admin:foodcartapp_product_change', args=(obj.id,))
        return format_html('<a href="{edit_url}"><img src="{src}" style="max-height: 50px;"/></a>', edit_url=edit_url, src=obj.image.url)
    get_image_list_preview.short_description = '????????????'


@admin.register(ProductCategory)
class ProductAdmin(admin.ModelAdmin):
    pass
