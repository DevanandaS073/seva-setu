import json
import re
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User

from .models import Branch, Donor, Donation, InventoryItem, Volunteer, Beneficiary, Expense, FundAllocation, AidDistribution, InventoryTransaction, Project, VolunteerAssignment
from .forms import (
    BranchForm, DonorForm, DonationForm, InventoryItemForm,
    VolunteerForm, BeneficiaryForm, ExpenseForm, FundAllocationForm, AidDistributionForm, InventoryTransactionForm, ProjectForm, VolunteerAssignmentForm,
    DonorRegistrationForm, DonorUpdateForm, DonorSelfDonationForm
)
from .utils import get_home_statistics, get_dashboard_statistics, generate_fund_utilization_pdf

# --- AUTH MIXINS & VIEWS ---

from django.conf import settings

class SuperUserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(f"{settings.LOGIN_URL}?next={self.request.path}")
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied


class PortalLoginView(LoginView):
    template_name = 'core/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        if self.request.user.is_superuser:
            return reverse_lazy('core:dashboard')
        try:
            donor = self.request.user.donor_profile
            return reverse_lazy('core:donor_dashboard')
        except Donor.DoesNotExist:
            return reverse_lazy('core:home')


class PortalLogoutView(LogoutView):
    next_page = 'core:home'


class DonorRegisterView(View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('core:home')
        form = DonorRegistrationForm()
        return render(request, 'core/register.html', {'form': form})

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('core:home')
        form = DonorRegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = User.objects.create_user(username=username, email=email, password=password)
            
            Donor.objects.create(
                user=user,
                name=form.cleaned_data['name'],
                email=email,
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address'],
                donor_type=Donor.DonorType.INDIVIDUAL
            )
            
            auth_login(request, user)
            messages.success(request, f"Welcome {user.username}! Your donor profile has been registered successfully.")
            return redirect('core:donor_dashboard')
        return render(request, 'core/register.html', {'form': form})


# --- CORE VIEWS ---

class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = get_home_statistics()
        return context


class DashboardView(SuperUserRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stats = get_dashboard_statistics()
        context.update(stats)
        
        # Serialize labels and values to JSON for safe insertion in Chart.js scripts
        context['branch_donation_labels_json'] = json.dumps(stats['branch_donation_labels'])
        context['branch_donation_values_json'] = json.dumps(stats['branch_donation_values'])
        context['category_expense_labels_json'] = json.dumps(stats['category_expense_labels'])
        context['category_expense_values_json'] = json.dumps(stats['category_expense_values'])
        context['trend_labels_json'] = json.dumps(stats['trend_labels'])
        context['trend_values_json'] = json.dumps(stats['trend_values'])
        context['volunteer_labels_json'] = json.dumps(stats['volunteer_labels'])
        context['volunteer_values_json'] = json.dumps(stats['volunteer_values'])
        context['meal_labels_json'] = json.dumps(stats['meal_labels'])
        context['meal_values_json'] = json.dumps(stats['meal_values'])
        context['inventory_labels_json'] = json.dumps(stats['inventory_labels'])
        context['inventory_values_json'] = json.dumps(stats['inventory_values'])
        context['project_expense_labels_json'] = json.dumps(stats['project_expense_labels'])
        context['project_expense_values_json'] = json.dumps(stats['project_expense_values'])
        
        return context


class PDFReportView(SuperUserRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="seva_setu_fund_utilization_report.pdf"'
        generate_fund_utilization_pdf(response)
        return response


# --- BRANCH CRUD ---

class BranchListView(SuperUserRequiredMixin, ListView):
    model = Branch
    template_name = 'core/branch_list.html'
    context_object_name = 'branches'


class BranchCreateView(SuperUserRequiredMixin, SuccessMessageMixin, CreateView):
    model = Branch
    form_class = BranchForm
    template_name = 'core/branch_form.html'
    success_url = reverse_lazy('core:branch_list')
    success_message = "Branch '%(name)s' was successfully created."


class BranchUpdateView(SuperUserRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Branch
    form_class = BranchForm
    template_name = 'core/branch_form.html'
    success_url = reverse_lazy('core:branch_list')
    success_message = "Branch '%(name)s' was successfully updated."


class BranchDeleteView(SuperUserRequiredMixin, DeleteView):
    model = Branch
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('core:branch_list')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, f"Branch '{obj.name}' was successfully deleted.")
        return super().delete(request, *args, **kwargs)


# --- DONOR CRUD ---

class DonorListView(SuperUserRequiredMixin, ListView):
    model = Donor
    template_name = 'core/donor_list.html'
    context_object_name = 'donors'


class DonorCreateView(SuperUserRequiredMixin, SuccessMessageMixin, CreateView):
    model = Donor
    form_class = DonorForm
    template_name = 'core/donor_form.html'
    success_url = reverse_lazy('core:donor_list')
    success_message = "Donor '%(name)s' was successfully registered."


class DonorUpdateView(SuperUserRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Donor
    form_class = DonorForm
    template_name = 'core/donor_form.html'
    success_url = reverse_lazy('core:donor_list')
    success_message = "Donor '%(name)s' was successfully updated."


class DonorDeleteView(SuperUserRequiredMixin, DeleteView):
    model = Donor
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('core:donor_list')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, f"Donor '{obj.name}' was successfully deleted.")
        return super().delete(request, *args, **kwargs)


# --- DONATION CRUD ---

class DonationListView(SuperUserRequiredMixin, ListView):
    model = Donation
    template_name = 'core/donation_list.html'
    context_object_name = 'donations'


class DonationCreateView(SuperUserRequiredMixin, SuccessMessageMixin, CreateView):
    model = Donation
    form_class = DonationForm
    template_name = 'core/donation_form.html'
    success_url = reverse_lazy('core:donation_list')
    success_message = "Donation of ₹%(amount)s was logged successfully."


class DonationUpdateView(SuperUserRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Donation
    form_class = DonationForm
    template_name = 'core/donation_form.html'
    success_url = reverse_lazy('core:donation_list')
    success_message = "Donation record was successfully updated."


class DonationDeleteView(SuperUserRequiredMixin, DeleteView):
    model = Donation
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('core:donation_list')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, f"Donation from '{obj.donor.name}' of ₹{obj.amount} was deleted.")
        return super().delete(request, *args, **kwargs)


# --- INVENTORY CRUD ---

class InventoryItemListView(SuperUserRequiredMixin, ListView):
    model = InventoryItem
    template_name = 'core/inventory_list.html'
    context_object_name = 'items'


class InventoryItemCreateView(SuperUserRequiredMixin, SuccessMessageMixin, CreateView):
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = 'core/inventory_form.html'
    success_url = reverse_lazy('core:inventory_list')
    success_message = "Inventory item '%(name)s' was added successfully."


class InventoryItemUpdateView(SuperUserRequiredMixin, SuccessMessageMixin, UpdateView):
    model = InventoryItem
    form_class = InventoryItemForm
    template_name = 'core/inventory_form.html'
    success_url = reverse_lazy('core:inventory_list')
    success_message = "Inventory item '%(name)s' was successfully updated."


class InventoryItemDeleteView(SuperUserRequiredMixin, DeleteView):
    model = InventoryItem
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('core:inventory_list')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, f"Inventory item '{obj.name}' at '{obj.branch.name}' was deleted.")
        return super().delete(request, *args, **kwargs)


# --- INVENTORY TRANSACTION CRUD ---

class InventoryTransactionListView(SuperUserRequiredMixin, ListView):
    model = InventoryTransaction
    template_name = 'core/inventorytransaction_list.html'
    context_object_name = 'transactions'

    def get_queryset(self):
        qs = super().get_queryset()
        item_id = self.request.GET.get('item')
        if item_id:
            qs = qs.filter(item_id=item_id)
        return qs


class InventoryTransactionCreateView(SuperUserRequiredMixin, SuccessMessageMixin, CreateView):
    model = InventoryTransaction
    form_class = InventoryTransactionForm
    template_name = 'core/inventorytransaction_form.html'
    success_url = reverse_lazy('core:inventorytransaction_list')
    success_message = "Inventory transaction logged successfully."


class InventoryTransactionUpdateView(SuperUserRequiredMixin, SuccessMessageMixin, UpdateView):
    model = InventoryTransaction
    form_class = InventoryTransactionForm
    template_name = 'core/inventorytransaction_form.html'
    success_url = reverse_lazy('core:inventorytransaction_list')
    success_message = "Inventory transaction updated successfully."


class InventoryTransactionDeleteView(SuperUserRequiredMixin, DeleteView):
    model = InventoryTransaction
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('core:inventorytransaction_list')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, f"Inventory transaction for '{obj.item.name}' was deleted.")
        return super().delete(request, *args, **kwargs)


# --- VOLUNTEER CRUD ---

class VolunteerListView(SuperUserRequiredMixin, ListView):
    model = Volunteer
    template_name = 'core/volunteer_list.html'
    context_object_name = 'volunteers'


class VolunteerCreateView(SuperUserRequiredMixin, SuccessMessageMixin, CreateView):
    model = Volunteer
    form_class = VolunteerForm
    template_name = 'core/volunteer_form.html'
    success_url = reverse_lazy('core:volunteer_list')
    success_message = "Volunteer '%(name)s' was successfully registered."


class VolunteerUpdateView(SuperUserRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Volunteer
    form_class = VolunteerForm
    template_name = 'core/volunteer_form.html'
    success_url = reverse_lazy('core:volunteer_list')
    success_message = "Volunteer '%(name)s' details were successfully updated."


class VolunteerDeleteView(SuperUserRequiredMixin, DeleteView):
    model = Volunteer
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('core:volunteer_list')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, f"Volunteer '{obj.name}' was deleted.")
        return super().delete(request, *args, **kwargs)


# --- BENEFICIARY CRUD ---

class BeneficiaryListView(SuperUserRequiredMixin, ListView):
    model = Beneficiary
    template_name = 'core/beneficiary_list.html'
    context_object_name = 'records'


class BeneficiaryCreateView(SuperUserRequiredMixin, SuccessMessageMixin, CreateView):
    model = Beneficiary
    form_class = BeneficiaryForm
    template_name = 'core/beneficiary_form.html'
    success_url = reverse_lazy('core:beneficiary_list')
    success_message = "Beneficiary '%(name)s' was successfully registered."


class BeneficiaryUpdateView(SuperUserRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Beneficiary
    form_class = BeneficiaryForm
    template_name = 'core/beneficiary_form.html'
    success_url = reverse_lazy('core:beneficiary_list')
    success_message = "Beneficiary profile was successfully updated."


class BeneficiaryDeleteView(SuperUserRequiredMixin, DeleteView):
    model = Beneficiary
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('core:beneficiary_list')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, f"Beneficiary profile for '{obj.name}' was deleted.")
        return super().delete(request, *args, **kwargs)


# --- AID DISTRIBUTION CRUD ---

class AidDistributionListView(SuperUserRequiredMixin, ListView):
    model = AidDistribution
    template_name = 'core/aiddistribution_list.html'
    context_object_name = 'distributions'


class AidDistributionCreateView(SuperUserRequiredMixin, SuccessMessageMixin, CreateView):
    model = AidDistribution
    form_class = AidDistributionForm
    template_name = 'core/aiddistribution_form.html'
    success_url = reverse_lazy('core:aiddistribution_list')
    success_message = "Aid distribution of %(quantity)s units was logged successfully."


class AidDistributionUpdateView(SuperUserRequiredMixin, SuccessMessageMixin, UpdateView):
    model = AidDistribution
    form_class = AidDistributionForm
    template_name = 'core/aiddistribution_form.html'
    success_url = reverse_lazy('core:aiddistribution_list')
    success_message = "Aid distribution details were successfully updated."


class AidDistributionDeleteView(SuperUserRequiredMixin, DeleteView):
    model = AidDistribution
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('core:aiddistribution_list')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, f"Aid distribution record for '{obj.beneficiary.name}' was deleted.")
        return super().delete(request, *args, **kwargs)


# --- EXPENSE CRUD ---

class ExpenseListView(SuperUserRequiredMixin, ListView):
    model = Expense
    template_name = 'core/expense_list.html'
    context_object_name = 'expenses'


class ExpenseCreateView(SuperUserRequiredMixin, SuccessMessageMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'core/expense_form.html'
    success_url = reverse_lazy('core:expense_list')
    success_message = "Expense of ₹%(amount)s was logged successfully."


class ExpenseUpdateView(SuperUserRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'core/expense_form.html'
    success_url = reverse_lazy('core:expense_list')
    success_message = "Expense details were successfully updated."


class ExpenseDeleteView(SuperUserRequiredMixin, DeleteView):
    model = Expense
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('core:expense_list')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, f"Expense record for '{obj.get_category_display()}' (₹{obj.amount}) was deleted.")
        return super().delete(request, *args, **kwargs)


# --- FUND ALLOCATION CRUD ---

class FundAllocationListView(SuperUserRequiredMixin, ListView):
    model = FundAllocation
    template_name = 'core/fundallocation_list.html'
    context_object_name = 'allocations'


class FundAllocationCreateView(SuperUserRequiredMixin, SuccessMessageMixin, CreateView):
    model = FundAllocation
    form_class = FundAllocationForm
    template_name = 'core/fundallocation_form.html'
    success_url = reverse_lazy('core:fundallocation_list')
    success_message = "Fund allocation of ₹%(amount)s was logged successfully."


class FundAllocationUpdateView(SuperUserRequiredMixin, SuccessMessageMixin, UpdateView):
    model = FundAllocation
    form_class = FundAllocationForm
    template_name = 'core/fundallocation_form.html'
    success_url = reverse_lazy('core:fundallocation_list')
    success_message = "Fund allocation details were successfully updated."


class FundAllocationDeleteView(SuperUserRequiredMixin, DeleteView):
    model = FundAllocation
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('core:fundallocation_list')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, f"Fund allocation of ₹{obj.amount} to '{obj.branch.name}' was deleted.")
        return super().delete(request, *args, **kwargs)


# --- PROJECT CRUD ---

class ProjectListView(SuperUserRequiredMixin, ListView):
    model = Project
    template_name = 'core/project_list.html'
    context_object_name = 'projects'


class ProjectCreateView(SuperUserRequiredMixin, SuccessMessageMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'core/project_form.html'
    success_url = reverse_lazy('core:project_list')
    success_message = "Project '%(name)s' was created successfully."


class ProjectUpdateView(SuperUserRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'core/project_form.html'
    success_url = reverse_lazy('core:project_list')
    success_message = "Project '%(name)s' details were updated successfully."


class ProjectDeleteView(SuperUserRequiredMixin, DeleteView):
    model = Project
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('core:project_list')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, f"Project '{obj.name}' was deleted.")
        return super().delete(request, *args, **kwargs)


# --- VOLUNTEER ASSIGNMENT CRUD ---

class VolunteerAssignmentListView(SuperUserRequiredMixin, ListView):
    model = VolunteerAssignment
    template_name = 'core/volunteerassignment_list.html'
    context_object_name = 'assignments'


class VolunteerAssignmentCreateView(SuperUserRequiredMixin, SuccessMessageMixin, CreateView):
    model = VolunteerAssignment
    form_class = VolunteerAssignmentForm
    template_name = 'core/volunteerassignment_form.html'
    success_url = reverse_lazy('core:volunteerassignment_list')
    success_message = "Volunteer assignment for %(volunteer)s was successfully logged."


class VolunteerAssignmentUpdateView(SuperUserRequiredMixin, SuccessMessageMixin, UpdateView):
    model = VolunteerAssignment
    form_class = VolunteerAssignmentForm
    template_name = 'core/volunteerassignment_form.html'
    success_url = reverse_lazy('core:volunteerassignment_list')
    success_message = "Volunteer assignment details were updated successfully."


class VolunteerAssignmentDeleteView(SuperUserRequiredMixin, DeleteView):
    model = VolunteerAssignment
    template_name = 'core/confirm_delete.html'
    success_url = reverse_lazy('core:volunteerassignment_list')

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        messages.success(self.request, f"Volunteer assignment for '{obj.volunteer.name}' was deleted.")
        return super().delete(request, *args, **kwargs)


# --- DONOR PORTAL VIEWS ---

class DonorDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'core/donor_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            donor = self.request.user.donor_profile
            context['donor'] = donor
            context['donations'] = donor.donations.all()
            
            import pandas as pd
            donations_qs = donor.donations.values('amount', 'donation_type')
            df = pd.DataFrame(list(donations_qs))
            if not df.empty:
                context['total_cash_donated'] = float(df[df['donation_type'] == 'cash']['amount'].sum())
                context['total_items_donated'] = int(df[df['donation_type'] == 'item'].shape[0])
            else:
                context['total_cash_donated'] = 0.00
                context['total_items_donated'] = 0
        except Donor.DoesNotExist:
            context['donor'] = None
            context['donations'] = []
            context['total_cash_donated'] = 0.00
            context['total_items_donated'] = 0
            
        return context


class DonorDonationCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Donation
    form_class = DonorSelfDonationForm
    template_name = 'core/donor_donation_form.html'
    success_url = reverse_lazy('core:donor_dashboard')
    success_message = "Thank you! Your donation contribution has been successfully logged."

    def form_valid(self, form):
        form.instance.donor = self.request.user.donor_profile
        return super().form_valid(form)


class DonorProfileUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Donor
    form_class = DonorUpdateForm
    template_name = 'core/donor_profile_form.html'
    success_url = reverse_lazy('core:donor_dashboard')
    success_message = "Your donor profile has been successfully updated."

    def get_object(self, queryset=None):
        return self.request.user.donor_profile


# --- ERROR HANDLERS ---

def custom_404(request, exception):
    return render(request, '404.html', status=404)


def custom_500(request):
    return render(request, '500.html', status=500)

