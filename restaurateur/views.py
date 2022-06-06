from collections import defaultdict
from operator import itemgetter

from django import forms
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from django.db.models import Prefetch
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from foodcartapp.models import Order, OrderItem, Product, Restaurant, RestaurantMenuItem
from locations.models import Location


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
    orders_serialized = []

    orders = (
        Order.objects.filter(status__in=(Order.Status.NEW, Order.Status.CONFIRMED))
        .annotate_price_total()
        .order_by('status', '-created_on')
        .select_related('assigned_restaurant')
        .prefetch_related(
            Prefetch(
                'items', 
                queryset=OrderItem.objects.select_related('product'), 
                to_attr='itemset')
            )
    )
    relevant_addresses = set([order.address for order in orders if order.assigned_restaurant is None])

    restaurants_with_items = RestaurantMenuItem.objects.get_restaurants_with_items()
    for restaurant in restaurants_with_items.keys():
        relevant_addresses.add(restaurant.address)

    relevant_locations = Location.objects.get_for_addresses(relevant_addresses)

    for order in orders:
        order_serialized = {
                'id': order.id,
                'status': order.get_status_display(),
                'payment_method': order.get_payment_method_display(),
                'price_total': order.price_total,
                'firstname':order.firstname,
                'lastname': order.lastname,
                'phonenumber': order.phonenumber,
                'address': order.address,
                'avaliable_for': None,
                'assigned_to': None,
                'note': order.note
            }

        if order.assigned_restaurant is not None:
            order_serialized['assigned_to'] = order.assigned_restaurant.name
        else:
            order_location = relevant_locations.get(order.address)

            order_items = [item.product.id for item in order.itemset]

            avaliable_restaurants = []

            for restaurant, items in restaurants_with_items.items():
                if not set(items).issuperset(order_items):
                    continue

                restaurant_location = relevant_locations.get(restaurant.address)
                distance = order_location.distance_to(restaurant_location)
                distance = round(distance, 3) if distance is not None else -1
                avaliable_restaurants.append(
                    {'name': restaurant.name, 'distance': distance}
                )

            order_serialized['avaliable_for'] = sorted(avaliable_restaurants, key=itemgetter('distance'))


        orders_serialized.append(order_serialized)


    return render(request, template_name='order_items.html', context={
        'orders': orders_serialized,
    })
