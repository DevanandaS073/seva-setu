from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # General
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('report/', views.PDFReportView.as_view(), name='download_report'),

    # Branch CRUD
    path('branches/', views.BranchListView.as_view(), name='branch_list'),
    path('branches/add/', views.BranchCreateView.as_view(), name='branch_create'),
    path('branches/<int:pk>/edit/', views.BranchUpdateView.as_view(), name='branch_update'),
    path('branches/<int:pk>/delete/', views.BranchDeleteView.as_view(), name='branch_delete'),

    # Donor CRUD
    path('donors/', views.DonorListView.as_view(), name='donor_list'),
    path('donors/add/', views.DonorCreateView.as_view(), name='donor_create'),
    path('donors/<int:pk>/edit/', views.DonorUpdateView.as_view(), name='donor_update'),
    path('donors/<int:pk>/delete/', views.DonorDeleteView.as_view(), name='donor_delete'),

    # Donation CRUD
    path('donations/', views.DonationListView.as_view(), name='donation_list'),
    path('donations/add/', views.DonationCreateView.as_view(), name='donation_create'),
    path('donations/<int:pk>/edit/', views.DonationUpdateView.as_view(), name='donation_update'),
    path('donations/<int:pk>/delete/', views.DonationDeleteView.as_view(), name='donation_delete'),

    # Inventory CRUD
    path('inventory/', views.InventoryItemListView.as_view(), name='inventory_list'),
    path('inventory/add/', views.InventoryItemCreateView.as_view(), name='inventory_create'),
    path('inventory/<int:pk>/edit/', views.InventoryItemUpdateView.as_view(), name='inventory_update'),
    path('inventory/<int:pk>/delete/', views.InventoryItemDeleteView.as_view(), name='inventory_delete'),

    # Inventory Transaction CRUD
    path('inventory/transactions/', views.InventoryTransactionListView.as_view(), name='inventorytransaction_list'),
    path('inventory/transactions/add/', views.InventoryTransactionCreateView.as_view(), name='inventorytransaction_create'),
    path('inventory/transactions/<int:pk>/edit/', views.InventoryTransactionUpdateView.as_view(), name='inventorytransaction_update'),
    path('inventory/transactions/<int:pk>/delete/', views.InventoryTransactionDeleteView.as_view(), name='inventorytransaction_delete'),

    # Volunteer CRUD
    path('volunteers/', views.VolunteerListView.as_view(), name='volunteer_list'),
    path('volunteers/add/', views.VolunteerCreateView.as_view(), name='volunteer_create'),
    path('volunteers/<int:pk>/edit/', views.VolunteerUpdateView.as_view(), name='volunteer_update'),
    path('volunteers/<int:pk>/delete/', views.VolunteerDeleteView.as_view(), name='volunteer_delete'),

    # Beneficiary CRUD
    path('beneficiaries/', views.BeneficiaryListView.as_view(), name='beneficiary_list'),
    path('beneficiaries/add/', views.BeneficiaryCreateView.as_view(), name='beneficiary_create'),
    path('beneficiaries/<int:pk>/edit/', views.BeneficiaryUpdateView.as_view(), name='beneficiary_update'),
    path('beneficiaries/<int:pk>/delete/', views.BeneficiaryDeleteView.as_view(), name='beneficiary_delete'),

    # Aid Distribution CRUD
    path('distributions/', views.AidDistributionListView.as_view(), name='aiddistribution_list'),
    path('distributions/add/', views.AidDistributionCreateView.as_view(), name='aiddistribution_create'),
    path('distributions/<int:pk>/edit/', views.AidDistributionUpdateView.as_view(), name='aiddistribution_update'),
    path('distributions/<int:pk>/delete/', views.AidDistributionDeleteView.as_view(), name='aiddistribution_delete'),

    # Expense CRUD
    path('expenses/', views.ExpenseListView.as_view(), name='expense_list'),
    path('expenses/add/', views.ExpenseCreateView.as_view(), name='expense_create'),
    path('expenses/<int:pk>/edit/', views.ExpenseUpdateView.as_view(), name='expense_update'),
    path('expenses/<int:pk>/delete/', views.ExpenseDeleteView.as_view(), name='expense_delete'),

    # Project CRUD
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/add/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_update'),
    path('projects/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),

    # Fund Allocation CRUD
    path('allocations/', views.FundAllocationListView.as_view(), name='fundallocation_list'),
    path('allocations/add/', views.FundAllocationCreateView.as_view(), name='fundallocation_create'),
    path('allocations/<int:pk>/edit/', views.FundAllocationUpdateView.as_view(), name='fundallocation_update'),
    path('allocations/<int:pk>/delete/', views.FundAllocationDeleteView.as_view(), name='fundallocation_delete'),

    # Volunteer Assignment CRUD
    path('volunteers/assignments/', views.VolunteerAssignmentListView.as_view(), name='volunteerassignment_list'),
    path('volunteers/assignments/add/', views.VolunteerAssignmentCreateView.as_view(), name='volunteerassignment_create'),
    path('volunteers/assignments/<int:pk>/edit/', views.VolunteerAssignmentUpdateView.as_view(), name='volunteerassignment_update'),
    path('volunteers/assignments/<int:pk>/delete/', views.VolunteerAssignmentDeleteView.as_view(), name='volunteerassignment_delete'),

    # Authentication & Registration
    path('login/', views.PortalLoginView.as_view(), name='login'),
    path('logout/', views.PortalLogoutView.as_view(), name='logout'),
    path('register/', views.DonorRegisterView.as_view(), name='register'),

    # Donor Portal
    path('donor/dashboard/', views.DonorDashboardView.as_view(), name='donor_dashboard'),
    path('donor/donations/add/', views.DonorDonationCreateView.as_view(), name='donor_donation_create'),
    path('donor/profile/edit/', views.DonorProfileUpdateView.as_view(), name='donor_profile_edit'),
]
