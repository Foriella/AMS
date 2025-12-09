from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Property, Unit, Tenant, Payment
from .forms import PropertyForm, UnitForm, TenantForm, PaymentForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect_user_dashboard(request.user)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user:
            login(request, user)
            name = user.first_name if user.first_name else user.username
            messages.success(request, f'Hey {name}, welcome back!')
            return redirect_user_dashboard(user)
        else:
            messages.error(request, 'Wrong username or password. Try again.')
    
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'Logged out.')
    return redirect('login')


def redirect_user_dashboard(user):
    if user.is_staff or user.is_superuser:
        return redirect('manager_dashboard')
    
    try:
        tenant = Tenant.objects.get(user=user)
        return redirect('tenant_dashboard_detail', pk=tenant.pk)
    except Tenant.DoesNotExist:
        return redirect('access_denied')


def access_denied(request):
    return render(request, 'access_denied.html')


def staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('access_denied')
        return view_func(request, *args, **kwargs)
    return wrapper


@staff_required
def property_list(request):
    properties = Property.objects.all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        properties = properties.filter(
            Q(name__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(city__icontains=search_query)
        )
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        properties = properties.filter(status=status_filter)
    
    type_filter = request.GET.get('type', '')
    if type_filter:
        properties = properties.filter(property_type=type_filter)
    
    total_properties = Property.objects.count()
    total_units = Property.objects.aggregate(total=Sum('total_units'))['total'] or 0
    active_properties = Property.objects.filter(status='active').count()
    
    context = {
        'properties': properties,
        'search_query': search_query,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'total_properties': total_properties,
        'total_units': total_units,
        'active_properties': active_properties,
        'form': PropertyForm(),
    }
    return render(request, 'properties/properties.html', context)


@staff_required
def property_create(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            prop = form.save()
            messages.success(request, f'Added {prop.name}')
            return redirect('property_list')
        else:
            messages.error(request, 'Check the form for errors.')
    else:
        form = PropertyForm()
    
    context = {'form': form}
    return render(request, 'properties/property_form.html', context)


@staff_required
def property_detail(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    context = {'property': property_obj}
    return render(request, 'properties/property_detail.html', context)


@staff_required
def property_update(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property_obj)
        if form.is_valid():
            form.save()
            messages.success(request, f'Updated {property_obj.name}')
            return redirect('property_list')
        else:
            messages.error(request, 'Fix the errors and try again.')
    else:
        form = PropertyForm(instance=property_obj)
    
    context = {
        'form': form,
        'property': property_obj,
        'is_edit': True
    }
    return render(request, 'properties/property_form.html', context)


@staff_required
def property_delete(request, pk):
    property_obj = get_object_or_404(Property, pk=pk)
    
    if request.method == 'POST':
        pname = property_obj.name
        property_obj.delete()
        messages.success(request, f'{pname} deleted')
        return redirect('property_list')
    
    context = {'property': property_obj}
    return render(request, 'properties/property_confirm_delete.html', context)


@staff_required
def unit_list(request):
    units = Unit.objects.select_related('property').all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        units = units.filter(
            Q(unit_number__icontains=search_query) |
            Q(property__name__icontains=search_query)
        )
    
    property_filter = request.GET.get('property', '')
    if property_filter:
        units = units.filter(property_id=property_filter)
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        units = units.filter(status=status_filter)
    
    type_filter = request.GET.get('type', '')
    if type_filter:
        units = units.filter(unit_type=type_filter)
    
    total_units = Unit.objects.count()
    occupied_units = Unit.objects.filter(is_occupied=True).count()
    available_units = Unit.objects.filter(status='available').count()
    
    context = {
        'units': units,
        'properties': Property.objects.all(),
        'search_query': search_query,
        'property_filter': property_filter,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'total_units': total_units,
        'occupied_units': occupied_units,
        'available_units': available_units,
        'form': UnitForm(),
    }
    return render(request, 'units/units.html', context)


@staff_required
def unit_create(request):
    if request.method == 'POST':
        form = UnitForm(request.POST)
        if form.is_valid():
            u = form.save()
            messages.success(request, f'Unit {u.unit_number} added')
            return redirect('unit_list')
        else:
            messages.error(request, 'Something went wrong. Check the form.')
    else:
        form = UnitForm()
    
    return render(request, 'units/unit_form.html', {'form': form})


@staff_required
def unit_detail(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    form = UnitForm(instance=unit)
    context = {'unit': unit, 'form': form, 'is_detail': True}
    return render(request, 'units/unit_form.html', context)


@staff_required
def unit_update(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    
    if request.method == 'POST':
        form = UnitForm(request.POST, instance=unit)
        if form.is_valid():
            form.save()
            messages.success(request, f'Unit {unit.unit_number} updated')
            return redirect('unit_list')
        else:
            messages.error(request, 'Fix errors below')
    else:
        form = UnitForm(instance=unit)
    
    ctx = {'form': form, 'unit': unit, 'is_edit': True}
    return render(request, 'units/unit_form.html', ctx)


@staff_required
def unit_delete(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    
    if request.method == 'POST':
        num = unit.unit_number
        unit.delete()
        messages.success(request, f'Unit {num} removed')
        return redirect('unit_list')
    
    return render(request, 'units/unit_confirm_delete.html', {'unit': unit})


@staff_required
def tenant_list(request):
    tenants = Tenant.objects.select_related('unit', 'unit__property').all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        tenants = tenants.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        tenants = tenants.filter(status=status_filter)
    
    property_filter = request.GET.get('property', '')
    if property_filter:
        tenants = tenants.filter(unit__property_id=property_filter)
    
    total_tenants = Tenant.objects.count()
    active_tenants = Tenant.objects.filter(status='active').count()
    pending_tenants = Tenant.objects.filter(status='pending').count()
    
    context = {
        'tenants': tenants,
        'properties': Property.objects.all(),
        'search_query': search_query,
        'status_filter': status_filter,
        'property_filter': property_filter,
        'total_tenants': total_tenants,
        'active_tenants': active_tenants,
        'pending_tenants': pending_tenants,
        'form': TenantForm(),
    }
    return render(request, 'tenants.html', context)


@staff_required
def tenant_create(request):
    if request.method == 'POST':
        post_data = request.POST.copy()
        
        user_selection = request.POST.get('user', '')
        new_username = request.POST.get('new_username', '').strip()
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if user_selection == 'create_new':
            post_data['user'] = ''  # Clear the invalid value
        
        form = TenantForm(post_data)
        
        new_user = None
        if user_selection == 'create_new':
            if not new_username:
                messages.error(request, 'Please enter a username for the new account.')
                return render(request, 'tenants/tenant_form.html', {
                    'form': form, 'create_new_account': True, 'new_username': new_username
                })
            
            if User.objects.filter(username=new_username).exists():
                messages.error(request, f'Username "{new_username}" is already taken. Please choose another.')
                return render(request, 'tenants/tenant_form.html', {
                    'form': form, 'create_new_account': True, 'new_username': new_username
                })
            
            if len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, 'tenants/tenant_form.html', {
                    'form': form, 'create_new_account': True, 'new_username': new_username
                })
            
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'tenants/tenant_form.html', {
                    'form': form, 'create_new_account': True, 'new_username': new_username
                })
            
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            email = request.POST.get('email', '')
            
            new_user = User.objects.create_user(
                username=new_username,
                password=new_password,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
        
        if form.is_valid():
            tenant = form.save(commit=False)
            
            if new_user:
                tenant.user = new_user
            
            tenant.save()
            
            if tenant.unit and tenant.status == 'active':
                tenant.unit.status = 'occupied'
                tenant.unit.save()
            
            success_message = f'Tenant "{tenant.full_name}" created successfully!'
            if new_user:
                success_message += f' Login account created with username: {new_username}'
            
            messages.success(request, success_message)
            return redirect('tenant_list')
        else:
            if new_user:
                new_user.delete()
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TenantForm()
    
    context = {'form': form}
    return render(request, 'tenants/tenant_form.html', context)


@staff_required
def tenant_detail(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    form = TenantForm(instance=tenant)
    context = {'tenant': tenant, 'form': form, 'is_detail': True}
    return render(request, 'tenants/tenant_form.html', context)


@staff_required
def tenant_update(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    
    if request.method == 'POST':
        post_data = request.POST.copy()
        
        user_selection = request.POST.get('user', '')
        new_username = request.POST.get('new_username', '').strip()
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if user_selection == 'create_new':
            post_data['user'] = ''
        
        form = TenantForm(post_data, instance=tenant)
        
        new_user = None
        if user_selection == 'create_new':
            if not new_username:
                messages.error(request, 'Please enter a username for the new account.')
                return render(request, 'tenants/tenant_form.html', {
                    'form': form, 'tenant': tenant, 'is_edit': True, 
                    'create_new_account': True, 'new_username': new_username
                })
            
            if User.objects.filter(username=new_username).exists():
                messages.error(request, f'Username "{new_username}" is already taken. Please choose another.')
                return render(request, 'tenants/tenant_form.html', {
                    'form': form, 'tenant': tenant, 'is_edit': True,
                    'create_new_account': True, 'new_username': new_username
                })
            
            if len(new_password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, 'tenants/tenant_form.html', {
                    'form': form, 'tenant': tenant, 'is_edit': True,
                    'create_new_account': True, 'new_username': new_username
                })
            
            if new_password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'tenants/tenant_form.html', {
                    'form': form, 'tenant': tenant, 'is_edit': True,
                    'create_new_account': True, 'new_username': new_username
                })
            
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            email = request.POST.get('email', '')
            
            new_user = User.objects.create_user(
                username=new_username,
                password=new_password,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
        
        if form.is_valid():
            tenant = form.save(commit=False)
            
            if new_user:
                tenant.user = new_user
            
            tenant.save()
            
            if tenant.unit and tenant.status == 'active':
                tenant.unit.status = 'occupied'
                tenant.unit.save()
            
            success_message = f'Tenant "{tenant.full_name}" updated successfully!'
            if new_user:
                success_message += f' Login account created with username: {new_username}'
            
            messages.success(request, success_message)
            return redirect('tenant_list')
        else:
            if new_user:
                new_user.delete()
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TenantForm(instance=tenant)
    
    context = {
        'form': form,
        'tenant': tenant,
        'is_edit': True
    }
    return render(request, 'tenants/tenant_form.html', context)


@staff_required
def tenant_delete(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    
    if request.method == 'POST':
        name = tenant.full_name
        if tenant.unit:
            tenant.unit.status = 'available'
            tenant.unit.save()
        tenant.delete()
        messages.success(request, f'{name} removed from tenants')
        return redirect('tenant_list')
    
    return render(request, 'tenants/tenant_confirm_delete.html', {'tenant': tenant})


@staff_required
def payment_list(request):
    payments = Payment.objects.select_related('tenant', 'tenant__unit', 'tenant__unit__property').all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        payments = payments.filter(
            Q(tenant__first_name__icontains=search_query) |
            Q(tenant__last_name__icontains=search_query) |
            Q(reference_number__icontains=search_query)
        )
    
    tenant_filter = request.GET.get('tenant', '')
    if tenant_filter:
        payments = payments.filter(tenant_id=tenant_filter)
    
    type_filter = request.GET.get('type', '')
    if type_filter:
        payments = payments.filter(payment_type=type_filter)
    
    method_filter = request.GET.get('method', '')
    if method_filter:
        payments = payments.filter(payment_method=method_filter)
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    total_payments = Payment.objects.count()
    total_collected = Payment.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
    pending_payments = Payment.objects.filter(status='pending').count()
    
    context = {
        'payments': payments,
        'tenants': Tenant.objects.filter(status='active'),
        'search_query': search_query,
        'tenant_filter': tenant_filter,
        'type_filter': type_filter,
        'method_filter': method_filter,
        'status_filter': status_filter,
        'total_payments': total_payments,
        'total_collected': total_collected,
        'pending_payments': pending_payments,
        'form': PaymentForm(),
    }
    return render(request, 'payments/payments.html', context)


@staff_required
def payment_create(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            p = form.save()
            messages.success(request, f'Payment of KES {p.amount} recorded')
            return redirect('payment_list')
        messages.error(request, 'Check the form')
    else:
        form = PaymentForm()
    
    return render(request, 'payments/payment_form.html', {'form': form})


@staff_required
def payment_detail(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    form = PaymentForm(instance=payment)
    context = {'payment': payment, 'form': form, 'is_detail': True}
    return render(request, 'payments/payment_form.html', context)


@staff_required
def payment_update(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment updated')
            return redirect('payment_list')
        messages.error(request, 'Fix the errors')
    else:
        form = PaymentForm(instance=payment)
    
    return render(request, 'payments/payment_form.html', {
        'form': form, 'payment': payment, 'is_edit': True
    })


@staff_required
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    
    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'Payment deleted successfully!')
        return redirect('payment_list')
    
    context = {'payment': payment}
    return render(request, 'payments/payment_confirm_delete.html', context)


@staff_required
def manager_dashboard(request):
    total_properties = Property.objects.count()
    active_properties = Property.objects.filter(status='active').count()
    
    total_units = Unit.objects.count()
    occupied_units = Unit.objects.filter(status='occupied').count()
    available_units = Unit.objects.filter(status='available').count()
    occupancy_rate = round((occupied_units / total_units * 100), 1) if total_units > 0 else 0
    
    total_tenants = Tenant.objects.count()
    active_tenants = Tenant.objects.filter(status='active').count()
    
    today = timezone.now().date()
    first_day_of_month = today.replace(day=1)
    monthly_collections = Payment.objects.filter(
        payment_date__gte=first_day_of_month,
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    pending_payments = Payment.objects.filter(status='pending').count()
    pending_amount = Payment.objects.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
    
    recent_payments = Payment.objects.select_related('tenant').order_by('-payment_date', '-created_at')[:5]
    
    properties = Property.objects.annotate(
        unit_count=Count('units'),
        occupied_count=Count('units', filter=Q(units__status='occupied'))
    )
    
    recent_tenants = Tenant.objects.select_related('unit', 'unit__property').order_by('-created_at')[:5]
    
    context = {
        'total_properties': total_properties,
        'active_properties': active_properties,
        'total_units': total_units,
        'occupied_units': occupied_units,
        'available_units': available_units,
        'occupancy_rate': occupancy_rate,
        'total_tenants': total_tenants,
        'active_tenants': active_tenants,
        'monthly_collections': monthly_collections,
        'pending_payments': pending_payments,
        'pending_amount': pending_amount,
        'recent_payments': recent_payments,
        'properties': properties,
        'recent_tenants': recent_tenants,
    }
    return render(request, 'dashboard/manager_dashboard.html', context)


@login_required(login_url='login')
def tenant_dashboard(request, pk=None):
    tenant = None
    
    if hasattr(request.user, 'tenant_profile'):
        tenant = request.user.tenant_profile
    elif pk and (request.user.is_staff or request.user.is_superuser):
        tenant = get_object_or_404(Tenant, pk=pk)
    else:
        messages.warning(request, 'No tenant profile linked to your account. Please contact the administrator.')
        return redirect('login')
    
    payments = Payment.objects.filter(tenant=tenant).order_by('-payment_date')[:10]
    
    total_paid = Payment.objects.filter(
        tenant=tenant, 
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    pending_amount = Payment.objects.filter(
        tenant=tenant, 
        status='pending'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    current_month = timezone.now().month
    current_year = timezone.now().year
    current_month_payment = Payment.objects.filter(
        tenant=tenant,
        payment_date__month=current_month,
        payment_date__year=current_year,
        payment_type='rent'
    ).first()
    
    today = timezone.now().date()
    days_until_lease_end = None
    lease_status = 'active'
    if tenant.lease_end_date:
        days_until_lease_end = (tenant.lease_end_date - today).days
        if days_until_lease_end < 0:
            lease_status = 'expired'
        elif days_until_lease_end <= 30:
            lease_status = 'expiring_soon'
    
    unit = tenant.unit
    property_obj = unit.property if unit else None
    
    context = {
        'tenant': tenant,
        'unit': unit,
        'property': property_obj,
        'payments': payments,
        'total_paid': total_paid,
        'pending_amount': pending_amount,
        'days_until_lease_end': days_until_lease_end,
        'lease_status': lease_status,
        'current_month_payment': current_month_payment,
        'rent_amount': tenant.rent_amount or (unit.rent_amount if unit else 0),
    }
    return render(request, 'dashboard/tenant_dashboard.html', context)


@staff_required
def financial_report(request):
    from django.db.models.functions import TruncMonth
    from datetime import datetime, timedelta
    
    year = request.GET.get('year', timezone.now().year)
    
    total_revenue = Payment.objects.filter(
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    current_month = timezone.now().month
    current_year = timezone.now().year
    monthly_revenue = Payment.objects.filter(
        status='completed',
        payment_date__month=current_month,
        payment_date__year=current_year
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    pending_payments = Payment.objects.filter(
        status='pending'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    monthly_data = Payment.objects.filter(
        status='completed',
        payment_date__year=current_year
    ).annotate(
        month=TruncMonth('payment_date')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')
    
    payment_by_type = Payment.objects.filter(
        status='completed'
    ).values('payment_type').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    recent_payments = Payment.objects.select_related('tenant').order_by('-payment_date')[:10]
    
    property_revenue = Payment.objects.filter(
        status='completed'
    ).values(
        'tenant__unit__property__name'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')[:5]
    
    total_expected_rent = Unit.objects.filter(status='occupied').aggregate(
        total=Sum('rent_amount')
    )['total'] or 0
    
    context = {
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'pending_payments': pending_payments,
        'monthly_data': list(monthly_data),
        'payment_by_type': list(payment_by_type),
        'recent_payments': recent_payments,
        'property_revenue': list(property_revenue),
        'total_expected_rent': total_expected_rent,
        'current_year': current_year,
    }
    return render(request, 'reports/financial_report.html', context)


@staff_required
def occupancy_report(request):
    total_units = Unit.objects.count()
    occupied_units = Unit.objects.filter(status='occupied').count()
    available_units = Unit.objects.filter(status='available').count()
    maintenance_units = Unit.objects.filter(status='maintenance').count()
    
    occupancy_rate = round((occupied_units / total_units * 100), 1) if total_units > 0 else 0
    
    properties = Property.objects.annotate(
        total_units_count=Count('units'),
        occupied_count=Count('units', filter=Q(units__status='occupied')),
        available_count=Count('units', filter=Q(units__status='available')),
    )
    
    for prop in properties:
        prop.occupancy_rate = round(
            (prop.occupied_count / prop.total_units_count * 100), 1
        ) if prop.total_units_count > 0 else 0
    
    unit_type_stats = Unit.objects.values('unit_type').annotate(
        total=Count('id'),
        occupied=Count('id', filter=Q(status='occupied')),
    )
    
    for stat in unit_type_stats:
        stat['occupancy_rate'] = round(
            (stat['occupied'] / stat['total'] * 100), 1
        ) if stat['total'] > 0 else 0
    
    total_tenants = Tenant.objects.count()
    active_tenants = Tenant.objects.filter(is_active=True).count()
    
    today = timezone.now().date()
    thirty_days = today + timedelta(days=30)
    expiring_leases = Tenant.objects.filter(
        lease_end_date__gte=today,
        lease_end_date__lte=thirty_days
    ).select_related('unit', 'unit__property')
    
    context = {
        'total_units': total_units,
        'occupied_units': occupied_units,
        'available_units': available_units,
        'maintenance_units': maintenance_units,
        'occupancy_rate': occupancy_rate,
        'properties': properties,
        'unit_type_stats': list(unit_type_stats),
        'total_tenants': total_tenants,
        'active_tenants': active_tenants,
        'expiring_leases': expiring_leases,
    }
    return render(request, 'reports/occupancy_report.html', context)


@login_required(login_url='login')
def mpesa_payment(request, tenant_id):
    tenant = get_object_or_404(Tenant, pk=tenant_id)
    
    if not request.user.is_staff and not request.user.is_superuser:
        if not hasattr(request.user, 'tenant_profile') or request.user.tenant_profile.pk != tenant_id:
            messages.error(request, 'You can only make payments for your own account.')
            return redirect('tenant_dashboard')
    
    unit = tenant.unit
    rent_amount = tenant.rent_amount or (unit.rent_amount if unit else 0)
    
    context = {
        'tenant': tenant,
        'unit': unit,
        'rent_amount': rent_amount,
    }
    return render(request, 'payments/mpesa_payment.html', context)


@login_required(login_url='login')
def mpesa_stk_push(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        from django_daraja.mpesa.core import MpesaClient
        
        data = json.loads(request.body)
        phone_number = data.get('phone_number')
        amount = data.get('amount')
        tenant_id = data.get('tenant_id')
        
        if not all([phone_number, amount, tenant_id]):
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
        
        phone_number = str(phone_number).strip()
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('+'):
            phone_number = phone_number[1:]
        
        if not phone_number.startswith('254'):
            phone_number = '254' + phone_number
        
        amount = int(float(amount))
        
        if amount < 1:
            return JsonResponse({'success': False, 'error': 'Amount must be at least 1 KES'}, status=400)
        
        cl = MpesaClient()
        account_reference = f'RENT-{tenant_id}'
        transaction_desc = f'Rent Payment for Tenant {tenant_id}'
        callback_url = 'https://mydomain.com/mpesa/callback/'
        
        response = cl.stk_push(
            phone_number=phone_number,
            amount=amount,
            account_reference=account_reference,
            transaction_desc=transaction_desc,
            callback_url=callback_url
        )
        
        if hasattr(response, 'response_code') and response.response_code == '0':
            return JsonResponse({
                'success': True,
                'message': 'STK Push sent successfully! Please check your phone and enter your M-Pesa PIN.',
                'checkout_request_id': getattr(response, 'checkout_request_id', None),
            })
        elif hasattr(response, 'error_code'):
            return JsonResponse({
                'success': False,
                'error': f"M-Pesa Error: {getattr(response, 'error_message', 'Unknown error')}"
            })
        else:
            response_dict = response.__dict__ if hasattr(response, '__dict__') else str(response)
            return JsonResponse({
                'success': True,
                'message': 'STK Push request sent. Check your phone for the M-Pesa prompt.',
                'debug': str(response_dict)
            })
        
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False, 
            'error': f'Error: {str(e)}',
            'trace': traceback.format_exc()
        }, status=500)


@csrf_exempt
def mpesa_callback(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            result_code = data.get('Body', {}).get('stkCallback', {}).get('ResultCode')
            result_desc = data.get('Body', {}).get('stkCallback', {}).get('ResultDesc')
            checkout_request_id = data.get('Body', {}).get('stkCallback', {}).get('CheckoutRequestID')
            
            if result_code == 0:
                callback_metadata = data.get('Body', {}).get('stkCallback', {}).get('CallbackMetadata', {}).get('Item', [])
                
                amount = None
                mpesa_receipt = None
                phone_number = None
                
                for item in callback_metadata:
                    if item.get('Name') == 'Amount':
                        amount = item.get('Value')
                    elif item.get('Name') == 'MpesaReceiptNumber':
                        mpesa_receipt = item.get('Value')
                    elif item.get('Name') == 'PhoneNumber':
                        phone_number = item.get('Value')
                
                tenant = Tenant.objects.filter(phone__endswith=str(phone_number)[-9:]).first()
                
                if tenant and amount:
                    Payment.objects.create(
                        tenant=tenant,
                        amount=amount,
                        payment_type='rent',
                        payment_method='mpesa',
                        payment_date=timezone.now().date(),
                        reference_number=mpesa_receipt or '',
                        description=f'M-Pesa payment - {checkout_request_id}',
                        status='completed'
                    )
            
            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
            
        except Exception as e:
            return JsonResponse({'ResultCode': 1, 'ResultDesc': str(e)})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)
