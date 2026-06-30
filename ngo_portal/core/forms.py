import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Branch, Donor, Donation, InventoryItem, Volunteer, Beneficiary, Expense, FundAllocation, AidDistribution, InventoryTransaction, Project, VolunteerAssignment

class BootstrapModelForm(forms.ModelForm):
    """Base ModelForm class to automatically apply Bootstrap 5 form classes."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.RadioSelect):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'


class BranchForm(BootstrapModelForm):
    class Meta:
        model = Branch
        fields = ['name', 'location', 'manager_name', 'phone']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Basic validation: check if phone contains only digits, +, -, and spaces
        if phone and not re.match(r'^\+?[0-9\s\-]{7,20}$', phone):
            raise ValidationError("Please enter a valid phone number.")
        return phone


class DonorForm(BootstrapModelForm):
    class Meta:
        model = Donor
        fields = ['name', 'email', 'phone', 'address', 'donor_type']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not re.match(r'^\+?[0-9\s\-]{7,20}$', phone):
            raise ValidationError("Please enter a valid phone number.")
        return phone


class DonationForm(BootstrapModelForm):
    class Meta:
        model = Donation
        fields = ['donor', 'donation_type', 'amount', 'payment_mode', 'item_category', 'item_name', 'item_quantity', 'item_unit', 'target_branch', 'date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        donation_type = cleaned_data.get('donation_type')
        amount = cleaned_data.get('amount')
        payment_mode = cleaned_data.get('payment_mode')
        item_category = cleaned_data.get('item_category')
        item_name = cleaned_data.get('item_name')
        item_quantity = cleaned_data.get('item_quantity')
        item_unit = cleaned_data.get('item_unit')
        target_branch = cleaned_data.get('target_branch')

        if donation_type == 'cash':
            if amount is None or amount <= 0:
                self.add_error('amount', "Donation amount is required and must be greater than zero for Cash donations.")
            if not payment_mode:
                self.add_error('payment_mode', "Payment mode is required for Cash donations.")
            
            cleaned_data['item_category'] = None
            cleaned_data['item_name'] = None
            cleaned_data['item_quantity'] = None
            cleaned_data['item_unit'] = None
            cleaned_data['target_branch'] = None
        else:
            if not item_name:
                self.add_error('item_name', "Item name is required for In-kind donations.")
            if not item_category:
                self.add_error('item_category', "Item category is required for In-kind donations.")
            if item_quantity is None or item_quantity <= 0:
                self.add_error('item_quantity', "Item quantity is required and must be greater than zero for In-kind donations.")
            if not item_unit:
                self.add_error('item_unit', "Item unit is required for In-kind donations.")
            if not target_branch:
                self.add_error('target_branch', "Target branch is required for In-kind donations.")
            
            cleaned_data['amount'] = None
            cleaned_data['payment_mode'] = None

        return cleaned_data


class InventoryItemForm(BootstrapModelForm):
    class Meta:
        model = InventoryItem
        fields = ['name', 'category', 'branch', 'unit']


class VolunteerForm(BootstrapModelForm):
    class Meta:
        model = Volunteer
        fields = ['name', 'email', 'phone', 'branch', 'skill', 'shift', 'join_date', 'is_active']
        widgets = {
            'join_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not re.match(r'^\+?[0-9\s\-]{7,20}$', phone):
            raise ValidationError("Please enter a valid phone number.")
        return phone


class BeneficiaryForm(BootstrapModelForm):
    class Meta:
        model = Beneficiary
        fields = ['name', 'email', 'phone', 'registered_branch', 'registered_date']
        widgets = {
            'registered_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not re.match(r'^\+?[0-9\s\-]{7,20}$', phone):
            raise ValidationError("Please enter a valid phone number.")
        return phone


class ExpenseForm(BootstrapModelForm):
    class Meta:
        model = Expense
        fields = ['project', 'branch', 'category', 'amount', 'date', 'description', 'receipt_number']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise ValidationError("Expense amount must be greater than zero.")
        return amount


class FundAllocationForm(BootstrapModelForm):
    class Meta:
        model = FundAllocation
        fields = ['donation', 'branch', 'amount', 'date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise ValidationError("Allocation amount must be greater than zero.")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        donation = cleaned_data.get('donation')
        amount = cleaned_data.get('amount')
        if donation and amount:
            existing_allocations = FundAllocation.objects.filter(donation=donation)
            if self.instance and self.instance.pk:
                existing_allocations = existing_allocations.exclude(pk=self.instance.pk)
            total_allocated = sum(item.amount for item in existing_allocations)
            remaining_amount = donation.amount - total_allocated
            if amount > remaining_amount:
                raise ValidationError(f"Cannot allocate Rs. {amount}. Only Rs. {remaining_amount:.2f} remains unallocated for this donation (Total donation amount: Rs. {donation.amount}).")
        return cleaned_data


class AidDistributionForm(BootstrapModelForm):
    class Meta:
        model = AidDistribution
        fields = ['beneficiary', 'branch', 'inventory_item', 'aid_type', 'meal_type', 'quantity', 'date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity <= 0:
            raise ValidationError("Quantity must be greater than zero.")
        return quantity

    def clean(self):
        cleaned_data = super().clean()
        aid_type = cleaned_data.get('aid_type')
        meal_type = cleaned_data.get('meal_type')
        branch = cleaned_data.get('branch')
        inventory_item = cleaned_data.get('inventory_item')
        quantity = cleaned_data.get('quantity')

        if aid_type == AidDistribution.AidType.MEAL:
            if not meal_type:
                self.add_error('meal_type', "Meal type is required for meal distributions.")
        else:
            cleaned_data['meal_type'] = None

        if inventory_item:
            # 1. Verify branch matches
            if branch and inventory_item.branch != branch:
                self.add_error('inventory_item', f"The selected inventory item '{inventory_item.name}' belongs to branch '{inventory_item.branch.name}', but this distribution is logged for branch '{branch.name}'. Items must match the operational branch.")
            
            # 2. Verify stock availability
            if quantity:
                from django.db.models import Sum
                tx_qs = InventoryTransaction.objects.filter(item=inventory_item)
                if self.instance and self.instance.inventory_transaction:
                    tx_qs = tx_qs.exclude(pk=self.instance.inventory_transaction.pk)
                
                in_sum = tx_qs.filter(transaction_type='in').aggregate(Sum('quantity'))['quantity__sum'] or 0
                out_sum = tx_qs.filter(transaction_type='out').aggregate(Sum('quantity'))['quantity__sum'] or 0
                available_stock = in_sum - out_sum

                if quantity > available_stock:
                    self.add_error('quantity', f"Insufficient stock. Selected inventory item '{inventory_item.name}' only has {available_stock} {inventory_item.unit} available, but you requested to allocate {quantity} {inventory_item.unit}.")

        return cleaned_data


class InventoryTransactionForm(BootstrapModelForm):
    class Meta:
        model = InventoryTransaction
        fields = ['item', 'transaction_type', 'quantity', 'date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity <= 0:
            raise ValidationError("Transaction quantity must be greater than zero.")
        return quantity

    def clean(self):
        cleaned_data = super().clean()
        item = cleaned_data.get('item')
        transaction_type = cleaned_data.get('transaction_type')
        quantity = cleaned_data.get('quantity')

        if item and transaction_type == InventoryTransaction.TransactionType.OUT and quantity:
            # Recalculate available stock excluding this transaction (if editing)
            from django.db.models import Sum
            existing_tx = InventoryTransaction.objects.filter(item=item)
            if self.instance and self.instance.pk:
                existing_tx = existing_tx.exclude(pk=self.instance.pk)
            in_sum = existing_tx.filter(transaction_type='in').aggregate(Sum('quantity'))['quantity__sum'] or 0
            out_sum = existing_tx.filter(transaction_type='out').aggregate(Sum('quantity'))['quantity__sum'] or 0
            current_stock = in_sum - out_sum

            if quantity > current_stock:
                raise ValidationError(f"Insufficient stock. Available stock for '{item.name}' is {current_stock} {item.unit}, but you requested to distribute {quantity} {item.unit}.")

        return cleaned_data


class ProjectForm(BootstrapModelForm):
    class Meta:
        model = Project
        fields = ['name', 'description', 'start_date', 'end_date', 'is_active']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', "End date cannot be earlier than the start date.")

        return cleaned_data


class VolunteerAssignmentForm(BootstrapModelForm):
    class Meta:
        model = VolunteerAssignment
        fields = ['volunteer', 'project', 'role', 'date_assigned', 'hours_spent', 'status']
        widgets = {
            'date_assigned': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_hours_spent(self):
        hours = self.cleaned_data.get('hours_spent')
        if hours is not None and hours < 0:
            raise ValidationError("Service hours contributed cannot be negative.")
        return hours


from django.contrib.auth.models import User

class DonorRegistrationForm(forms.Form):
    username = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))
    
    name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}))
    phone = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}))
    address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Residential Address', 'rows': 3}))

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("A user with this email address is already registered.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not re.match(r'^\+?[0-9\s\-]{7,20}$', phone):
            raise ValidationError("Please enter a valid phone number.")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

        return cleaned_data


class DonorUpdateForm(BootstrapModelForm):
    class Meta:
        model = Donor
        fields = ['name', 'phone', 'address']


class DonorSelfDonationForm(BootstrapModelForm):
    class Meta:
        model = Donation
        fields = ['donation_type', 'amount', 'payment_mode', 'item_category', 'item_name', 'item_quantity', 'item_unit', 'target_branch', 'date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        donation_type = cleaned_data.get('donation_type')
        amount = cleaned_data.get('amount')
        payment_mode = cleaned_data.get('payment_mode')
        item_category = cleaned_data.get('item_category')
        item_name = cleaned_data.get('item_name')
        item_quantity = cleaned_data.get('item_quantity')
        item_unit = cleaned_data.get('item_unit')
        target_branch = cleaned_data.get('target_branch')

        if donation_type == 'cash':
            if amount is None or amount <= 0:
                self.add_error('amount', "Donation amount is required and must be greater than zero for Cash donations.")
            if not payment_mode:
                self.add_error('payment_mode', "Payment mode is required for Cash donations.")
            
            cleaned_data['item_category'] = None
            cleaned_data['item_name'] = None
            cleaned_data['item_quantity'] = None
            cleaned_data['item_unit'] = None
            cleaned_data['target_branch'] = None
        else:
            if not item_name:
                self.add_error('item_name', "Item name is required for In-kind donations.")
            if not item_category:
                self.add_error('item_category', "Item category is required for In-kind donations.")
            if item_quantity is None or item_quantity <= 0:
                self.add_error('item_quantity', "Item quantity is required and must be greater than zero for In-kind donations.")
            if not item_unit:
                self.add_error('item_unit', "Item unit is required for In-kind donations.")
            if not target_branch:
                self.add_error('target_branch', "Target branch is required for In-kind donations.")
            
            cleaned_data['amount'] = None
            cleaned_data['payment_mode'] = None

        return cleaned_data
