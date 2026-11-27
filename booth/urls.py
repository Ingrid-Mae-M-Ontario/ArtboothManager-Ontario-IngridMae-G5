from django.urls import path

from booth import views, views_sales

app_name = 'booth'

urlpatterns = [
    path('items/', views.ItemListView.as_view(), name='item_list'),
    path('items/new/', views.ItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/edit/', views.ItemUpdateView.as_view(), name='item_update'),
    path('items/<int:pk>/delete/', views.ItemDeleteView.as_view(), name='item_delete'),
    path('events/', views.EventListView.as_view(), name='event_list'),
    path('events/new/', views.EventCreateView.as_view(), name='event_create'),
    path('events/<int:pk>/edit/', views.EventUpdateView.as_view(), name='event_update'),
    path('events/<int:pk>/delete/', views.EventDeleteView.as_view(), name='event_delete'),
    path('events/<int:event_id>/inventory/', views_sales.event_inventory, name='event_inventory'),
    path('inventory/<int:pk>/edit/', views_sales.InventoryUpdateView.as_view(), name='inventory_update'),
    path('inventory/<int:pk>/delete/', views_sales.InventoryDeleteView.as_view(), name='inventory_delete'),
    path('events/<int:event_id>/sell/', views_sales.record_sale, name='record_sale'),
    path('sales/', views_sales.sale_list, name='sale_list'),
    path('sales/<int:pk>/', views_sales.sale_detail, name='sale_detail'),
    path('sales/<int:pk>/void/', views_sales.void_sale, name='void_sale'),
]