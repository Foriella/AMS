from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login_page'),
    path('logout/', views.logout_view, name='logout'),
    path('access-denied/', views.access_denied, name='access_denied'),
    
    path('dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('manager-dashboard/', views.manager_dashboard, name='dashboard'),
    path('tenant-dashboard/', views.tenant_dashboard, name='tenant_dashboard'),
    path('tenant-dashboard/<int:pk>/', views.tenant_dashboard, name='tenant_dashboard_detail'),
    
    path('properties/', views.property_list, name='property_list'),
    path('properties/create/', views.property_create, name='property_create'),
    path('properties/<int:pk>/', views.property_detail, name='property_detail'),
    path('properties/<int:pk>/edit/', views.property_update, name='property_update'),
    path('properties/<int:pk>/delete/', views.property_delete, name='property_delete'),
    
    path('units/', views.unit_list, name='unit_list'),
    path('units/create/', views.unit_create, name='unit_create'),
    path('units/<int:pk>/', views.unit_detail, name='unit_detail'),
    path('units/<int:pk>/edit/', views.unit_update, name='unit_update'),
    path('units/<int:pk>/delete/', views.unit_delete, name='unit_delete'),
    
    path('tenants/', views.tenant_list, name='tenant_list'),
    path('tenants/create/', views.tenant_create, name='tenant_create'),
    path('tenants/<int:pk>/', views.tenant_detail, name='tenant_detail'),
    path('tenants/<int:pk>/edit/', views.tenant_update, name='tenant_update'),
    path('tenants/<int:pk>/delete/', views.tenant_delete, name='tenant_delete'),
    
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/create/', views.payment_create, name='payment_create'),
    path('payments/<int:pk>/', views.payment_detail, name='payment_detail'),
    path('payments/<int:pk>/edit/', views.payment_update, name='payment_update'),
    path('payments/<int:pk>/delete/', views.payment_delete, name='payment_delete'),
    
    path('reports/financial/', views.financial_report, name='financial_report'),
    path('reports/occupancy/', views.occupancy_report, name='occupancy_report'),
    
    path('mpesa/payment/<int:tenant_id>/', views.mpesa_payment, name='mpesa_payment'),
    path('mpesa/stk-push/', views.mpesa_stk_push, name='mpesa_stk_push'),
    path('mpesa/callback/', views.mpesa_callback, name='mpesa_callback'),
]
