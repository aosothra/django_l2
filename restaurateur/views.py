from collections import defaultdict
from django import forms
from django.db.models import Prefetch
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views


from foodcartapp.models import Order, OrderItem, Product, Restaurant, RestaurantMenuItem


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    default_availability = {restaurant.id: False for restaurant in restaurants}
    products_with_restaurants = []
    for product in products:

        availability = {
            **default_availability,
            **{item.restaurant_id: item.availability for item in product.menu_items.all()},
        }
        orderer_availability = [availability[restaurant.id] for restaurant in restaurants]

        products_with_restaurants.append(
            (product, orderer_availability)
        )

    return render(request, template_name="products_list.html", context={
        'products_with_restaurants': products_with_restaurants,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    order_items_query = OrderItem.objects.select_related('product')
    orders = (
        Order.objects.filter(status__in=(Order.Status.NEW, Order.Status.CONFIRMED))
        .price_sum()
        .order_by('status', '-created_on')
        .select_related('assigned_restaurant')
        .prefetch_related(Prefetch('items', queryset=order_items_query, to_attr='itemset'))
    )

    items_in_restaurants = defaultdict(list)
    
    for entry in RestaurantMenuItem.objects.select_related('restaurant').select_related('product').filter(availability=True):
        items_in_restaurants[entry.restaurant].append(entry.product.id)

    orders_serialized = []
    for order in orders:
        if order.assigned_restaurant is None:
            order_items = [item.product.id for item in order.itemset]

            restaurants = [
                restaurant for restaurant, items in items_in_restaurants.items()
                if set(items).issuperset(order_items)
            ]

            assignment = 'Доступно для: ' + ', '.join([restaurant.name for restaurant in restaurants])
        else:
            assignment = f'Готовится в {order.assigned_restaurant.name}'

        orders_serialized.append(
            {
                'id': order.id,
                'status': order.get_status_display(),
                'payment_method': order.get_payment_method_display(),
                'price_total': order.price_total,
                'firstname':order.firstname,
                'lastname': order.lastname,
                'phonenumber': order.phonenumber,
                'address': order.address,
                'assignment': assignment,
                'note': order.note
            }
        )


    return render(request, template_name='order_items.html', context={
        'order_items': orders_serialized,
    })
