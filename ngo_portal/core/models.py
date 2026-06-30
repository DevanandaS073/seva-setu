from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator
from django.utils import timezone

class Branch(models.Model):
    name = models.CharField(max_length=100, unique=True)
    location = models.CharField(max_length=200)
    manager_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)

    class Meta:
        verbose_name_plural = "Branches"
        ordering = ['name']

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    class Role(models.TextChoices):
        SUPER_ADMIN = 'super_admin', 'Super Admin'
        BRANCH_HEAD = 'branch_head', 'Branch Head'
        DONOR = 'donor', 'Donor'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.DONOR)
    branch = models.ForeignKey(Branch, null=True, blank=True, on_delete=models.SET_NULL, related_name='branch_heads')

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


class Donor(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name='donor_profile')

    class DonorType(models.TextChoices):
        INDIVIDUAL = 'individual', 'Individual'
        CORPORATE = 'corporate', 'Corporate'

    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    donor_type = models.CharField(
        max_length=20,
        choices=DonorType.choices,
        default=DonorType.INDIVIDUAL
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_donor_type_display()})"


class Donation(models.Model):
    class PaymentMode(models.TextChoices):
        CASH = 'cash', 'Cash'
        ONLINE = 'online', 'Online'
        CHEQUE = 'cheque', 'Cheque'

    class DonationType(models.TextChoices):
        CASH = 'cash', 'Cash'
        ITEM = 'item', 'Item / In-kind'

    class ItemCategory(models.TextChoices):
        FOOD = 'food', 'Food'
        MEDICINE = 'medicine', 'Medicine'
        CLOTHING = 'clothing', 'Clothing'
        OTHER = 'other', 'Other'

    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='donations')
    donation_type = models.CharField(
        max_length=20,
        choices=DonationType.choices,
        default=DonationType.CASH
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    date = models.DateField(default=timezone.now)
    payment_mode = models.CharField(
        max_length=20,
        choices=PaymentMode.choices,
        blank=True,
        null=True
    )
    item_category = models.CharField(
        max_length=20,
        choices=ItemCategory.choices,
        blank=True,
        null=True
    )
    item_name = models.CharField(max_length=100, blank=True, null=True)
    item_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0.01)]
    )
    item_unit = models.CharField(max_length=20, blank=True, null=True)
    target_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, blank=True, null=True, related_name='item_donations')
    inventory_transaction = models.OneToOneField('InventoryTransaction', on_delete=models.SET_NULL, blank=True, null=True, related_name='source_donation')
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date', '-id']

    @property
    def allocated_amount(self):
        return sum(a.amount for a in self.allocations.all())

    def __str__(self):
        if self.donation_type == self.DonationType.CASH:
            return f"{self.donor.name} - Cash: Rs. {self.amount} ({self.date})"
        else:
            return f"{self.donor.name} - Item: {self.item_quantity} {self.item_unit} of {self.item_name} ({self.date})"

    def save(self, *args, **kwargs):
        if self.donation_type == self.DonationType.ITEM:
            self.amount = 0.00
            self.payment_mode = None
            super().save(*args, **kwargs)
            
            item, created = InventoryItem.objects.get_or_create(
                branch=self.target_branch,
                name=self.item_name,
                category=self.item_category,
                defaults={'unit': self.item_unit, 'quantity': 0.0}
            )
            
            if self.inventory_transaction:
                tx = self.inventory_transaction
                tx.item = item
                tx.quantity = self.item_quantity
                tx.date = self.date
                tx.notes = f"In-Kind donation from {self.donor.name} (Donation #{self.pk})"
                tx.save()
            else:
                tx = InventoryTransaction.objects.create(
                    item=item,
                    transaction_type='in',
                    quantity=self.item_quantity,
                    date=self.date,
                    notes=f"In-Kind donation from {self.donor.name} (Donation #{self.pk})"
                )
                Donation.objects.filter(pk=self.pk).update(inventory_transaction=tx)
                self.inventory_transaction = tx
        else:
            if self.inventory_transaction:
                tx = self.inventory_transaction
                Donation.objects.filter(pk=self.pk).update(inventory_transaction=None)
                self.inventory_transaction = None
                tx.delete()
            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        tx = self.inventory_transaction
        super().delete(*args, **kwargs)
        if tx:
            tx.delete()


class FundAllocation(models.Model):
    donation = models.ForeignKey(Donation, on_delete=models.CASCADE, related_name='allocations')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='allocations')
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"Allocation of Rs. {self.amount} to {self.branch.name} from donation ID {self.donation.id}"


class InventoryItem(models.Model):
    class Category(models.TextChoices):
        FOOD = 'food', 'Food'
        MEDICINE = 'medicine', 'Medicine'
        CLOTHING = 'clothing', 'Clothing'
        OTHER = 'other', 'Other'

    name = models.CharField(max_length=100)
    category = models.CharField(
        max_length=20,
        choices=Category.choices
    )
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='inventory_items')
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        validators=[MinValueValidator(0.0)]
    )
    unit = models.CharField(max_length=20)  # kg, litres, pieces, etc.
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('name', 'branch')
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit}) at {self.branch.name}"


class InventoryTransaction(models.Model):
    class TransactionType(models.TextChoices):
        IN = 'in', 'Stock In (Receive / Purchase)'
        OUT = 'out', 'Stock Out (Distribute / Spoilage)'

    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        default=TransactionType.IN
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.quantity} {self.item.unit} of {self.item.name} ({self.date})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.recalculate_item_stock()

    def delete(self, *args, **kwargs):
        item = self.item
        super().delete(*args, **kwargs)
        # Recalculate stock
        from django.db.models import Sum
        in_sum = InventoryTransaction.objects.filter(item=item, transaction_type='in').aggregate(Sum('quantity'))['quantity__sum'] or 0
        out_sum = InventoryTransaction.objects.filter(item=item, transaction_type='out').aggregate(Sum('quantity'))['quantity__sum'] or 0
        item.quantity = in_sum - out_sum
        item.save()

    def recalculate_item_stock(self):
        from django.db.models import Sum
        in_sum = InventoryTransaction.objects.filter(item=self.item, transaction_type='in').aggregate(Sum('quantity'))['quantity__sum'] or 0
        out_sum = InventoryTransaction.objects.filter(item=self.item, transaction_type='out').aggregate(Sum('quantity'))['quantity__sum'] or 0
        self.item.quantity = in_sum - out_sum
        self.item.save()


class Volunteer(models.Model):
    class Shift(models.TextChoices):
        MORNING = 'morning', 'Morning'
        AFTERNOON = 'afternoon', 'Afternoon'
        EVENING = 'evening', 'Evening'

    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='volunteers')
    skill = models.CharField(max_length=100)
    shift = models.CharField(
        max_length=20,
        choices=Shift.choices
    )
    join_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    donor = models.ForeignKey(Donor, null=True, blank=True, on_delete=models.SET_NULL, related_name='volunteer_signups')

    class Meta:
        ordering = ['name']

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.name} - {self.branch.name} ({status})"


class Beneficiary(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    registered_branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='registered_beneficiaries')
    registered_date = models.DateField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Beneficiaries"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} (Reg: {self.registered_branch.name})"


class AidDistribution(models.Model):
    class AidType(models.TextChoices):
        MEAL = 'meal', 'Meal'
        MEDICINE = 'medicine', 'Medicine'
        CLOTHING = 'clothing', 'Clothing'
        OTHER = 'other', 'Other'

    class MealType(models.TextChoices):
        BREAKFAST = 'breakfast', 'Breakfast'
        LUNCH = 'lunch', 'Lunch'
        DINNER = 'dinner', 'Dinner'

    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, related_name='distributions')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='distributions')
    inventory_item = models.ForeignKey(InventoryItem, on_delete=models.SET_NULL, blank=True, null=True, related_name='aid_distributions')
    inventory_transaction = models.OneToOneField(InventoryTransaction, on_delete=models.SET_NULL, blank=True, null=True, related_name='aid_distribution')
    date = models.DateField(default=timezone.now)
    aid_type = models.CharField(
        max_length=20,
        choices=AidType.choices,
        default=AidType.MEAL
    )
    meal_type = models.CharField(
        max_length=20,
        choices=MealType.choices,
        blank=True,
        null=True
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        desc = f"Served {self.get_aid_type_display()}"
        if self.aid_type == self.AidType.MEAL and self.meal_type:
            desc += f" ({self.get_meal_type_display()})"
        return f"{self.beneficiary.name} - {desc} at {self.branch.name} ({self.date})"

    def save(self, *args, **kwargs):
        # Save first to establish primary key for notes description
        super().save(*args, **kwargs)
        
        if self.inventory_item:
            if self.inventory_transaction:
                tx = self.inventory_transaction
                tx.item = self.inventory_item
                tx.quantity = self.quantity
                tx.date = self.date
                tx.notes = f"Allocated to beneficiary: {self.beneficiary.name} (via Aid Distribution #{self.pk})"
                tx.save()
            else:
                tx = InventoryTransaction.objects.create(
                    item=self.inventory_item,
                    transaction_type='out',
                    quantity=self.quantity,
                    date=self.date,
                    notes=f"Allocated to beneficiary: {self.beneficiary.name} (via Aid Distribution #{self.pk})"
                )
                AidDistribution.objects.filter(pk=self.pk).update(inventory_transaction=tx)
                self.inventory_transaction = tx
        else:
            if self.inventory_transaction:
                tx = self.inventory_transaction
                AidDistribution.objects.filter(pk=self.pk).update(inventory_transaction=None)
                self.inventory_transaction = None
                tx.delete()

    def delete(self, *args, **kwargs):
        tx = self.inventory_transaction
        super().delete(*args, **kwargs)
        if tx:
            tx.delete()


class Project(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.name} ({status})"

    @property
    def total_expenses(self):
        return sum(expense.amount for expense in self.expenses.all())


class Expense(models.Model):
    class Category(models.TextChoices):
        FOOD = 'food', 'Food'
        TRANSPORT = 'transport', 'Transport'
        STAFF = 'staff', 'Staff'
        UTILITIES = 'utilities', 'Utilities'
        OTHER = 'other', 'Other'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='expenses')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='expenses')
    category = models.CharField(
        max_length=20,
        choices=Category.choices
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    date = models.DateField(default=timezone.now)
    description = models.TextField()
    receipt_number = models.CharField(max_length=50)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.get_category_display()} - {self.amount} for {self.project.name} at {self.branch.name} ({self.date})"


class VolunteerAssignment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE, related_name='assignments')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='assignments')
    role = models.CharField(max_length=100)
    date_assigned = models.DateField(default=timezone.now)
    hours_spent = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of volunteer hours contributed"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    class Meta:
        ordering = ['-date_assigned', '-id']

    def __str__(self):
        return f"{self.volunteer.name} assigned to {self.project.name} as {self.role} ({self.get_status_display()})"
