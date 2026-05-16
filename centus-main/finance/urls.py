from django.urls import path
from . import views

urlpatterns = [
    path('', views.transaction_list, name='transaction_list'),
    path('add/', views.transaction_create, name='transaction_create'),
    path('register/', views.register, name='register'),
    path('analysis/', views.analysis, name='analysis'),  
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_create, name='category_create'),
    path('categories/edit/<int:pk>/', views.category_update, name='category_update'),
    path('categories/delete/<int:pk>/', views.category_delete, name='category_delete'),
    path('edit/<int:pk>/', views.transaction_update, name='transaction_update'),
    path('delete/<int:pk>/', views.transaction_delete, name='transaction_delete'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('recommendations/', views.recommendations_view, name='recommendations'),
    path("limits/", views.budget_limits_list, name="budget_limits"),
    path("limits/add/", views.budget_limit_create, name="budget_limit_create"),
    path("limits/edit/<int:pk>/", views.budget_limit_update, name="budget_limit_update"),
    path("limits/delete/<int:pk>/", views.budget_limit_delete, name="budget_limit_delete"),
    path('upload-receipt/', views.upload_receipt, name='upload_receipt'),
    path('receipts/', views.receipt_list, name='receipt_list'),
    path('receipts/delete/<int:pk>/', views.receipt_delete, name='receipt_delete'),
    path('receipts/', views.receipt_list, name='receipt_list'),
    path('receipt/review/<int:receipt_id>/', views.review_receipt, name='review_receipt'),
]