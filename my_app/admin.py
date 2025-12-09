from django.contrib import admin
from django.contrib.admin import AdminSite
from django import forms
from .models import Property, Unit, Tenant, Payment

AdminSite.actions_selection_counter = True
AdminSite.empty_value_display = ''


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ['name', 'property_type', 'city', 'total_units', 'tenant_count', 'status']
    list_filter = ['status', 'property_type', 'city']
    search_fields = ['name', 'address', 'city']
    ordering = ['-created_at']
    
    actions_on_top = False
    actions_on_bottom = False
    
    def tenant_count(self, obj):
        """Count tenants in this property"""
        return Tenant.objects.filter(unit__property=obj).count()
    tenant_count.short_description = 'Tenants'


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['unit_number', 'property', 'unit_type', 'rent_amount', 'status']
    list_filter = ['status', 'unit_type', 'property']
    search_fields = ['unit_number', 'property__name']
    ordering = ['property', 'unit_number']
    
    exclude = ['is_occupied']
    
    actions_on_top = False
    actions_on_bottom = False
    
    class Media:
        css = {
            'all': ('style/admin.css',)
        }
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Remove dashed line from Property dropdown - show blank instead"""
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if field:
            field.empty_label = ''  # Blank instead of dashes
        return field


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'phone', 'unit', 'status']
    list_filter = ['status', 'unit__property']
    search_fields = ['first_name', 'last_name', 'email', 'phone']
    ordering = ['last_name', 'first_name']
    
    actions_on_top = False
    actions_on_bottom = False
    
    class Media:
        css = {
            'all': ('style/admin.css',)
        }
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Use plain text input for date fields (no calendar icon)"""
        if db_field.name in ['lease_start_date', 'lease_end_date']:
            kwargs['widget'] = forms.TextInput(attrs={'placeholder': 'YYYY-MM-DD'})
        return super().formfield_for_dbfield(db_field, request, **kwargs)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Remove dashed line from dropdowns - show blank instead"""
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if field:
            field.empty_label = ''
        return field
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Name'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'amount', 'payment_type', 'payment_method', 'payment_date', 'status']
    list_filter = ['status', 'payment_type', 'payment_method', 'payment_date']
    search_fields = ['tenant__first_name', 'tenant__last_name', 'reference_number']
    ordering = ['-payment_date', '-created_at']
    date_hierarchy = 'payment_date'
    
    actions_on_top = False
    actions_on_bottom = False
    
    class Media:
        css = {
            'all': ('style/admin.css',)
        }
    
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Use plain text input for date fields (no calendar icon)"""
        if db_field.name in ['payment_date', 'period_start', 'period_end']:
            kwargs['widget'] = forms.TextInput(attrs={'placeholder': 'YYYY-MM-DD'})
        return super().formfield_for_dbfield(db_field, request, **kwargs)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Remove dashed line from dropdowns - show blank instead"""
        field = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if field:
            field.empty_label = ''
        return field

