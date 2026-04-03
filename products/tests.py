from django.test import TestCase

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Category, Product

class ProductCatalogTests(APITestCase):
    def setUp(self):
        """Подготовка данных"""
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
        """Проверяем получение списка категорий"""
        url = reverse('category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], "Электроника")
    
    def test_get_product_list(self):
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
    
    def test_search_product(self):
        response = self.client.get(self.url, {'search': 'Xiaomi'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], "Xiaomi 15")
    
    def test_get_product(self):
        url = reverse('product-detail', kwargs={'pk': self.product1.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], "Xiaomi 15")
