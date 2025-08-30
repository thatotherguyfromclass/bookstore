# store/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.catalog, name='catalog'),
    path('cart/', views.cart_page, name='cart'),
    path('checkout/', views.checkout_page, name='checkout'),

    # API endpoints
    path('api/checkout/create-order/', views.create_order, name='create_order'),
    path('api/payments/verify/', views.verify_payment, name='verify_payment'),

    # Thank you page
    path('thank-you/<str:reference>/', views.thank_you, name='thank_you'),
]
