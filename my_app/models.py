from django.db import models
from django.contrib.auth.models import User


class Property(models.Model):
    PROPERTY_TYPES = [
        ('apartment', 'Apartment Building'),
        ('house', 'House'),
        ('commercial', 'Commercial Building'),
        ('mixed', 'Mixed Use'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance'),
    ]
    
    name = models.CharField(max_length=200)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES, default='apartment')
    address = models.TextField()
    city = models.CharField(max_length=100)
    county = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    total_units = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_properties')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Properties"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def occupied_units(self):
        return self.units.filter(is_occupied=True).count()
    
    @property
    def vacant_units(self):
        return self.units.filter(is_occupied=False).count()
    
    @property
    def occupancy_rate(self):
        if not self.total_units:
            return 0
        return round(self.occupied_units / self.total_units * 100, 1)


class Unit(models.Model):
    UNIT_TYPES = [
        ('studio', 'Studio'),
        ('1br', '1 Bedroom'),
        ('2br', '2 Bedroom'),
        ('3br', '3 Bedroom'),
        ('4br', '4 Bedroom'),
        ('penthouse', 'Penthouse'),
        ('commercial', 'Commercial Space'),
    ]
    
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Under Maintenance'),
        ('reserved', 'Reserved'),
    ]
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='units')
    unit_number = models.CharField(max_length=20)
    unit_type = models.CharField(max_length=20, choices=UNIT_TYPES, default='1br')
    floor = models.CharField(max_length=20, blank=True)
    bedrooms = models.PositiveIntegerField(default=1)
    bathrooms = models.PositiveIntegerField(default=1)
   
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    is_occupied = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['property', 'unit_number']
        unique_together = ['property', 'unit_number']
    
    def __str__(self):
        return f"{self.property.name} - Unit {self.unit_number}"
    
    def save(self, *args, **kwargs):
        self.is_occupied = self.status == 'occupied'
        super().save(*args, **kwargs)


class Tenant(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tenant_profile')
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    id_number = models.CharField(max_length=50, blank=True)
    
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name='tenants')
    
    lease_start_date = models.DateField(null=True, blank=True)
    lease_end_date = models.DateField(null=True, blank=True)
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    deposit_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def property_name(self):
        if self.unit:
            return self.unit.property.name
        return None


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('mpesa', 'M-Pesa'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    PAYMENT_TYPES = [
        ('rent', 'Rent'),
        ('deposit', 'Deposit'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='rent')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='mpesa')
    payment_date = models.DateField()
    reference_number = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-payment_date', '-created_at']
    
    def __str__(self):
        return f"{self.tenant.full_name} - {self.payment_type} - {self.amount}"
    
    @property
    def property_name(self):
        try:
            return self.tenant.unit.property.name
        except:
            return None
