from django.contrib import admin
from django.db.models import Sum
from .models import Branch, Donor, Donation, InventoryItem, Volunteer, Beneficiary, Expense, FundAllocation, AidDistribution, InventoryTransaction, Project, VolunteerAssignment

class FundAllocationInline(admin.TabularInline):
    model = FundAllocation
    extra = 1


class AidDistributionInline(admin.TabularInline):
    model = AidDistribution
    extra = 1


class InventoryTransactionInline(admin.TabularInline):
    model = InventoryTransaction
    extra = 1


class ExpenseInline(admin.TabularInline):
    model = Expense
    extra = 1


class VolunteerAssignmentInline(admin.TabularInline):
    model = VolunteerAssignment
    extra = 1


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'manager_name', 'phone')
    search_fields = ('name', 'manager_name', 'location')
    ordering = ('name',)


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'donor_type')
    search_fields = ('name', 'email', 'phone')
    list_filter = ('donor_type',)
    ordering = ('name',)


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('donor', 'amount', 'date', 'payment_mode')
    list_filter = ('payment_mode', 'date')
    search_fields = ('donor__name', 'notes')
    ordering = ('-date', '-id')
    inlines = [FundAllocationInline]

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        try:
            # We construct the changelist to get the filtered queryset
            ChangeList = self.get_changelist(request)
            cl = ChangeList(
                request, self.model, self.list_display,
                self.list_display_links, self.list_filter, self.date_hierarchy,
                self.search_fields, self.list_select_related, self.list_per_page,
                self.list_max_show_all, self.list_editable, self, self.sortable_by,
                self.search_help_text
            )
            queryset = cl.get_queryset(request)
            total = queryset.aggregate(Sum('amount'))['amount__sum'] or 0
        except Exception:
            total = Donation.objects.aggregate(Sum('amount'))['amount__sum'] or 0
        
        extra_context['total_donations_sum'] = total
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(FundAllocation)
class FundAllocationAdmin(admin.ModelAdmin):
    list_display = ('donation', 'branch', 'amount', 'date')
    list_filter = ('branch', 'date')
    search_fields = ('donation__donor__name', 'notes')
    ordering = ('-date', '-id')


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'branch', 'quantity', 'unit', 'last_updated')
    list_filter = ('branch', 'category')
    search_fields = ('name',)
    ordering = ('branch', 'category', 'name')
    inlines = [InventoryTransactionInline]


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ('item', 'transaction_type', 'quantity', 'date')
    list_filter = ('transaction_type', 'date', 'item__branch')
    search_fields = ('item__name', 'notes')
    ordering = ('-date', '-id')


@admin.register(Volunteer)
class VolunteerAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'shift', 'is_active', 'phone')
    list_filter = ('branch', 'shift', 'is_active')
    search_fields = ('name', 'email', 'phone', 'skill')
    actions = ['make_active', 'make_inactive']
    ordering = ('name',)
    inlines = [VolunteerAssignmentInline]

    @admin.action(description="Mark selected volunteers as active")
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Successfully marked {updated} volunteers as active.")

    @admin.action(description="Mark selected volunteers as inactive")
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Successfully marked {updated} volunteers as inactive.")


@admin.register(Beneficiary)
class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'registered_branch', 'registered_date')
    list_filter = ('registered_branch', 'registered_date')
    search_fields = ('name', 'email', 'phone')
    ordering = ('name',)
    inlines = [AidDistributionInline]


@admin.register(AidDistribution)
class AidDistributionAdmin(admin.ModelAdmin):
    list_display = ('beneficiary', 'branch', 'inventory_item', 'date', 'aid_type', 'meal_type', 'quantity')
    list_filter = ('branch', 'inventory_item', 'aid_type', 'meal_type', 'date')
    search_fields = ('beneficiary__name', 'notes')
    ordering = ('-date', '-id')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'start_date')
    search_fields = ('name', 'description')
    ordering = ('name',)
    inlines = [ExpenseInline, VolunteerAssignmentInline]


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('project', 'branch', 'category', 'amount', 'date', 'receipt_number')
    list_filter = ('project', 'branch', 'category', 'date')
    search_fields = ('description', 'receipt_number')
    ordering = ('-date', '-id')


@admin.register(VolunteerAssignment)
class VolunteerAssignmentAdmin(admin.ModelAdmin):
    list_display = ('volunteer', 'project', 'role', 'date_assigned', 'hours_spent', 'status')
    list_filter = ('project', 'status', 'date_assigned')
    search_fields = ('volunteer__name', 'role')
    ordering = ('-date_assigned', '-id')
