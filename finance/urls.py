from django.urls import path
from . import views # <--- Tutaj ta kropka jest poprawna, bo views.py jest w tym samym folderze (finance)

urlpatterns = [
    # name='transaction_list' jest ważne, bo używamy go w redirectach
    path('', views.transaction_list, name='transaction_list'),
    path('add/', views.transaction_create, name='transaction_create'),
    path('register/', views.register, name='register'),
]