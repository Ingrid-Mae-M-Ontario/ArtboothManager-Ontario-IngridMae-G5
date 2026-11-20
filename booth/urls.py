from django.urls import path

from booth import views

app_name = 'booth'

urlpatterns = [
    path('my-events/', views.AssistantEventListView.as_view(), name='assistant_event_list'),
    path('items/', views.ItemListView.as_view(), name='item_list'),
    path('items/new/', views.ItemCreateView.as_view(), name='item_create'),
    path('items/<int:pk>/edit/', views.ItemUpdateView.as_view(), name='item_update'),
    path('items/<int:pk>/delete/', views.ItemDeleteView.as_view(), name='item_delete'),
    path('events/', views.EventListView.as_view(), name='event_list'),
    path('events/new/', views.EventCreateView.as_view(), name='event_create'),
    path('events/<int:pk>/edit/', views.EventUpdateView.as_view(), name='event_update'),
    path('events/<int:pk>/delete/', views.EventDeleteView.as_view(), name='event_delete'),
    path('events/<int:event_pk>/stock/', views.EventStockListView.as_view(), name='stock_list'),
    path('events/<int:event_pk>/stock/new/', views.EventStockCreateView.as_view(), name='stock_create'),
    path(
        'events/<int:event_pk>/stock/<int:pk>/edit/',
        views.EventStockUpdateView.as_view(), name='stock_update',
    ),
    path(
        'events/<int:event_pk>/stock/<int:pk>/delete/',
        views.EventStockDeleteView.as_view(), name='stock_delete',
    ),
    path('events/<int:event_pk>/sales/', views.SalesListView.as_view(), name='sales_list'),
    path('events/<int:event_pk>/sales/new/', views.SaleCreateView.as_view(), name='sale_create'),
    path(
        'events/<int:event_pk>/sales/<int:pk>/void/',
        views.SaleVoidView.as_view(), name='sale_void',
    ),
]