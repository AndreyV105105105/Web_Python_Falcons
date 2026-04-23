from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Category, Product, Cart, CartItem

class ProductCatalogTests(APITestCase):
    def setUp(self):
        """Подготовка данных"""
        self.user = User.objects.create_user(username='Legenda', password='67try')
        self.client.force_authenticate(user=self.user)
        self.category = Category.objects.create(name="Электроника", slug="electronics")
        self.product1 = Product.objects.create(
            name="Xiaomi 15",
            price=100000,
            category=self.category,
            quantity=10,
            is_available=True
        )
        self.product2 = Product.objects.create(
            name="MacBook",
            price=200000,
            category=self.category,
            quantity=5,
            is_available=True
        )

        self.url = reverse('product-list')
    
    def test_get_category_list(self):
        url = reverse('category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], "Электроника")
    
    def test_get_product_list(self):
        """Проверяет получение списка товаров"""

        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
    
    def test_search_product(self):
        """Проверяет работу поиска товаров"""

        response = self.client.get(self.url, {'search': 'Xiaomi'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], "Xiaomi 15")
    
    def test_get_product(self):
        """Проверяет получение товара"""

        url = reverse('product-detail', kwargs={'pk': self.product1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Xiaomi 15")

    def test_add_to_cart_success(self):
        url = reverse('cartitem-list')
        data = {'product': self.product1.id, 'quantity': 2}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CartItem.objects.count(), 1)

    def test_checkout_decreases_stock(self):
        cart, _ = Cart.objects.get_or_create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product1, quantity=3)

        url = reverse('order-checkout')
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.product1.refresh_from_db()
        self.assertEqual(self.product1.quantity, 7)