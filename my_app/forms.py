from django import forms
from django.contrib.auth.models import User
from .models import Property, Unit, Tenant, Payment


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = ['name', 'property_type', 'address', 'city', 'county', 
                  'description', 'total_units', 'status', 'manager']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            widget = self.fields[field].widget
            if isinstance(widget, forms.Select):
                widget.attrs['class'] = 'form-select'
            else:
                widget.attrs['class'] = 'form-control'
        
        self.fields['address'].widget.attrs['rows'] = 2
        self.fields['description'].widget.attrs['rows'] = 3
        self.fields['total_units'].widget.attrs['min'] = 0


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['property', 'unit_number', 'unit_type', 'floor', 'bedrooms', 
                  'bathrooms', 'rent_amount', 'deposit_amount', 'status', 'description']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            w = field.widget
            w.attrs['class'] = 'form-select' if isinstance(w, forms.Select) else 'form-control'
        
        self.fields['description'].widget.attrs['rows'] = 3
        self.fields['bedrooms'].widget.attrs['min'] = 0
        self.fields['bathrooms'].widget.attrs['min'] = 0


class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = ['user', 'first_name', 'last_name', 'email', 'phone', 'id_number',
                  'unit', 'lease_start_date', 'lease_end_date', 'rent_amount', 
                  'deposit_paid', 'emergency_contact_name', 'emergency_contact_phone',
                  'status', 'notes']
        widgets = {
            'lease_start_date': forms.DateInput(attrs={'type': 'date'}),
            'lease_end_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            if isinstance(f.widget, forms.Select):
                f.widget.attrs['class'] = 'form-select'
            else:
                f.widget.attrs['class'] = 'form-control'
        self.fields['notes'].widget.attrs['rows'] = 3


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['tenant', 'amount', 'payment_type', 'payment_method', 
                  'payment_date', 'reference_number', 'description', 'status',
                  'period_start', 'period_end']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'period_start': forms.DateInput(attrs={'type': 'date'}),
            'period_end': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            cls = 'form-select' if isinstance(f.widget, forms.Select) else 'form-control'
            f.widget.attrs['class'] = cls
        self.fields['description'].widget.attrs['rows'] = 2
