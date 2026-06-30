import datetime
import pandas as pd
from django.db.models import Sum, Count
from django.utils import timezone
from .models import Branch, Donor, Donation, InventoryItem, Volunteer, Beneficiary, Expense, FundAllocation, AidDistribution, Project, VolunteerAssignment

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def get_home_statistics():
    """Calculate summary statistics for the home page using Django ORM and Pandas."""
    # Fetch data as list of values for Pandas DataFrame creation
    donations_qs = Donation.objects.values('amount')
    expenses_qs = Expense.objects.values('amount')
    volunteers_qs = Volunteer.objects.values('is_active')
    beneficiaries_qs = Beneficiary.objects.values('id')
    inventory_qs = InventoryItem.objects.values('id')
    branches_qs = Branch.objects.values('id')
    projects_qs = Project.objects.values('id')
    assignments_qs = VolunteerAssignment.objects.values('hours_spent')

    # Convert to DataFrames
    df_donations = pd.DataFrame(list(donations_qs))
    df_expenses = pd.DataFrame(list(expenses_qs))
    df_volunteers = pd.DataFrame(list(volunteers_qs))
    df_beneficiaries = pd.DataFrame(list(beneficiaries_qs))
    df_inventory = pd.DataFrame(list(inventory_qs))
    df_branches = pd.DataFrame(list(branches_qs))
    df_projects = pd.DataFrame(list(projects_qs))
    df_assignments = pd.DataFrame(list(assignments_qs))

    # Aggregate using Pandas
    total_donations = float(df_donations['amount'].sum()) if not df_donations.empty else 0.0
    total_expenses = float(df_expenses['amount'].sum()) if not df_expenses.empty else 0.0
    total_volunteers = int(df_volunteers[df_volunteers['is_active'] == True].shape[0]) if not df_volunteers.empty else 0
    total_beneficiaries = int(df_beneficiaries.shape[0]) if not df_beneficiaries.empty else 0
    total_inventory = int(df_inventory.shape[0]) if not df_inventory.empty else 0
    total_branches = int(df_branches.shape[0]) if not df_branches.empty else 0
    total_projects = int(df_projects.shape[0]) if not df_projects.empty else 0
    total_hours = int(df_assignments['hours_spent'].sum()) if not df_assignments.empty else 0

    return {
        'total_donations': total_donations,
        'total_volunteers': total_volunteers,
        'total_beneficiaries': total_beneficiaries,
        'total_inventory': total_inventory,
        'total_expenses': total_expenses,
        'total_branches': total_branches,
        'total_projects': total_projects,
        'total_hours': total_hours,
    }


def get_dashboard_statistics():
    """Retrieve and process analytics data using Pandas for the Impact Dashboard."""
    # 1. Branch-wise Fund Allocations
    allocations_qs = FundAllocation.objects.values('branch__name', 'amount')
    df_allocations = pd.DataFrame(list(allocations_qs))
    
    if not df_allocations.empty:
        branch_donations = df_allocations.groupby('branch__name')['amount'].sum().reset_index()
        branch_donations = branch_donations.sort_values(by='amount', ascending=False)
        branch_donation_labels = branch_donations['branch__name'].tolist()
        branch_donation_values = [float(val) for val in branch_donations['amount'].tolist()]
    else:
        branch_donation_labels, branch_donation_values = [], []

    # 2. Category-wise and Project-wise Expenses
    expenses_qs = Expense.objects.values('category', 'amount', 'project__name')
    df_expenses = pd.DataFrame(list(expenses_qs))
    
    if not df_expenses.empty:
        category_expenses = df_expenses.groupby('category')['amount'].sum().reset_index()
        category_expenses = category_expenses.sort_values(by='amount', ascending=False)
        category_expense_labels = [cat.capitalize() for cat in category_expenses['category'].tolist()]
        category_expense_values = [float(val) for val in category_expenses['amount'].tolist()]

        project_expenses = df_expenses.groupby('project__name')['amount'].sum().reset_index()
        project_expenses = project_expenses.sort_values(by='amount', ascending=False)
        project_expense_labels = project_expenses['project__name'].tolist()
        project_expense_values = [float(val) for val in project_expenses['amount'].tolist()]
    else:
        category_expense_labels, category_expense_values = [], []
        project_expense_labels, project_expense_values = [], []

    # 3. Monthly Donation Trend (Last 6 Months)
    six_months_ago = timezone.now().date() - datetime.timedelta(days=180)
    trend_qs = Donation.objects.filter(date__gte=six_months_ago).values('date', 'amount')
    df_trend = pd.DataFrame(list(trend_qs))
    
    if not df_trend.empty:
        # Convert date to datetime and create month periods
        df_trend['date_dt'] = pd.to_datetime(df_trend['date'])
        df_trend['month_period'] = df_trend['date_dt'].dt.to_period('M')
        
        grouped_trend = df_trend.groupby('month_period')['amount'].sum().reset_index()
        grouped_trend = grouped_trend.sort_values('month_period')
        
        trend_labels = grouped_trend['month_period'].dt.strftime('%b %Y').tolist()
        trend_values = [float(val) for val in grouped_trend['amount'].tolist()]
    else:
        trend_labels, trend_values = [], []

    # 4. Volunteer Statistics (Active vs Inactive)
    volunteers_qs = Volunteer.objects.values('is_active')
    df_volunteers = pd.DataFrame(list(volunteers_qs))
    
    if not df_volunteers.empty:
        vol_stats = df_volunteers.groupby('is_active').size().reset_index(name='count')
        vol_labels = ['Active' if active else 'Inactive' for active in vol_stats['is_active'].tolist()]
        vol_values = vol_stats['count'].tolist()
    else:
        vol_labels, vol_values = [], []

    # 5. Beneficiary Meal-type Distribution
    ben_qs = AidDistribution.objects.filter(aid_type='meal').values('meal_type', 'quantity')
    df_ben = pd.DataFrame(list(ben_qs))
    
    if not df_ben.empty:
        meal_stats = df_ben.groupby('meal_type')['quantity'].sum().reset_index()
        meal_labels = [meal.capitalize() for meal in meal_stats['meal_type'].tolist()]
        meal_values = [int(val) for val in meal_stats['quantity'].tolist()]
    else:
        meal_labels, meal_values = [], []

    # 6. Inventory Category Summaries
    inventory_qs = InventoryItem.objects.values('category', 'quantity')
    df_inventory = pd.DataFrame(list(inventory_qs))
    
    if not df_inventory.empty:
        inv_stats = df_inventory.groupby('category')['quantity'].sum().reset_index()
        inv_labels = [cat.capitalize() for cat in inv_stats['category'].tolist()]
        inv_values = [float(val) for val in inv_stats['quantity'].tolist()]
    else:
        inv_labels, inv_values = [], []

    # 7. Top 5 Donors by Total Amount
    donor_donations_qs = Donation.objects.values('donor__name', 'donor__email', 'donor__donor_type', 'amount')
    df_donor_donations = pd.DataFrame(list(donor_donations_qs))
    
    top_donors_list = []
    if not df_donor_donations.empty:
        grouped_donors = df_donor_donations.groupby(
            ['donor__name', 'donor__email', 'donor__donor_type']
        )['amount'].sum().reset_index()
        
        grouped_donors = grouped_donors.sort_values(by='amount', ascending=False).head(5)
        for _, row in grouped_donors.iterrows():
            top_donors_list.append({
                'name': row['donor__name'],
                'email': row['donor__email'],
                'type': 'Individual' if row['donor__donor_type'] == 'individual' else 'Corporate',
                'total_amount': float(row['amount'])
            })

    # 8. Volunteer Count per Branch
    vol_branch_qs = Volunteer.objects.values('branch__name')
    df_vol_branch = pd.DataFrame(list(vol_branch_qs))
    branch_volunteers = []
    if not df_vol_branch.empty:
        grouped_vol_branch = df_vol_branch.groupby('branch__name').size().reset_index(name='volunteer_count')
        grouped_vol_branch = grouped_vol_branch.sort_values(by='volunteer_count', ascending=False)
        branch_volunteers = grouped_vol_branch.to_dict(orient='records')

    # 9. Beneficiary Count per Branch (served counts)
    ben_branch_qs = AidDistribution.objects.values('branch__name', 'quantity')
    df_ben_branch = pd.DataFrame(list(ben_branch_qs))
    branch_beneficiaries = []
    if not df_ben_branch.empty:
        grouped_ben_branch = df_ben_branch.groupby('branch__name')['quantity'].sum().reset_index(name='served_count')
        grouped_ben_branch = grouped_ben_branch.sort_values(by='served_count', ascending=False)
        grouped_ben_branch['served_count'] = grouped_ben_branch['served_count'].astype(int)
        branch_beneficiaries = grouped_ben_branch.to_dict(orient='records')

    return {
        'branch_donation_labels': branch_donation_labels,
        'branch_donation_values': branch_donation_values,
        'category_expense_labels': category_expense_labels,
        'category_expense_values': category_expense_values,
        'project_expense_labels': project_expense_labels,
        'project_expense_values': project_expense_values,
        'trend_labels': trend_labels,
        'trend_values': trend_values,
        'volunteer_labels': vol_labels,
        'volunteer_values': vol_values,
        'meal_labels': meal_labels,
        'meal_values': meal_values,
        'inventory_labels': inv_labels,
        'inventory_values': inv_values,
        'branch_volunteers': branch_volunteers,
        'branch_beneficiaries': branch_beneficiaries,
        'top_donors': top_donors_list,
    }


from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Custom canvas subclass that handles dynamic total page numbering in a two-pass render."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        # Draw top accent bar (navy blue)
        self.setFillColor(colors.HexColor('#1e3a8a'))
        self.rect(0, 772, 612, 20, fill=True, stroke=False)
        
        # Draw bottom accent line
        self.setStrokeColor(colors.HexColor('#e2e8f0'))
        self.setLineWidth(1)
        self.line(54, 40, 558, 40)
        
        # Draw running footer text
        self.setFont('Helvetica-Bold', 8)
        self.setFillColor(colors.HexColor('#64748b'))
        self.drawString(54, 25, "CONFIDENTIAL - SEVA SETU PORTAL")
        
        self.setFont('Helvetica', 8)
        self.drawRightString(558, 25, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def generate_fund_utilization_pdf(response):
    """Generates the professional fund utilization PDF report using ReportLab and writes it to the response."""
    # Set up the document
    doc = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=60,
        bottomMargin=60
    )
    
    # Get statistics
    home_stats = get_home_statistics()
    dash_stats = get_dashboard_statistics()
    
    # Style definitions
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=5
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'),
        spaceAfter=20
    )
    
    h1_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#334155'),
        spaceAfter=12
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )
    
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#0f172a')
    )

    story = []
    
    # Header block
    story.append(Paragraph("Seva Setu", title_style))
    story.append(Paragraph("NGO Resource & Donation Management Portal — Fund Utilization Report", subtitle_style))
    
    # Report Meta Table (Width: 504 pt)
    meta_data = [
        [Paragraph("<b>Report Date:</b>", table_cell_style), Paragraph(timezone.now().strftime('%B %d, %Y %I:%M %p'), table_cell_style)],
        [Paragraph("<b>Security Classification:</b>", table_cell_style), Paragraph("<font color='#dc2626'><b>Confidential / Internal Use Only</b></font>", table_cell_style)],
        [Paragraph("<b>Data Status:</b>", table_cell_style), Paragraph("<font color='#16a34a'><b>Live Verified (ORM Aggregates)</b></font>", table_cell_style)],
    ]
    meta_table = Table(meta_data, colWidths=[130, 374])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # Executive Summary (Net Balance)
    story.append(Paragraph("1. Executive Financial Summary", h1_style))
    
    total_donations = float(home_stats['total_donations'])
    total_expenses = float(home_stats['total_expenses'])
    net_balance = total_donations - total_expenses
    
    balance_color = '#16a34a' if net_balance >= 0 else '#dc2626'
    
    summary_data = [
        [Paragraph("<b>Total Contributions</b>", table_header_style), Paragraph("<b>Total Expenditures</b>", table_header_style), Paragraph("<b>Net Reserve Balance</b>", table_header_style)],
        [Paragraph(f"Rs. {total_donations:,.2f}", table_cell_style), Paragraph(f"Rs. {total_expenses:,.2f}", table_cell_style), Paragraph(f"<font color='{balance_color}'><b>Rs. {net_balance:,.2f}</b></font>", table_cell_style)]
    ]
    summary_table = Table(summary_data, colWidths=[168, 168, 168])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#f8fafc')),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))
    
    # Branch Donations Table (Width: 504 pt)
    story.append(Paragraph("2. Branch-wise Fund Allocations", h1_style))
    donations_data = [[Paragraph("<b>Branch Name</b>", table_header_style), Paragraph("<b>Total Allocated Funds</b>", table_header_style)]]
    
    for i, label in enumerate(dash_stats['branch_donation_labels']):
        amount = dash_stats['branch_donation_values'][i]
        donations_data.append([
            Paragraph(label, table_cell_style),
            Paragraph(f"Rs. {amount:,.2f}", table_cell_style)
        ])
    
    if len(donations_data) == 1:
        donations_data.append([Paragraph("No fund allocations available", table_cell_style), Paragraph("Rs. 0.00", table_cell_style)])
        
    donations_table = Table(donations_data, colWidths=[252, 252])
    donations_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#334155')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    story.append(donations_table)
    
    # Page Break to separate sections cleanly
    story.append(PageBreak())
    
    # Top Donors Table (Width: 504 pt)
    story.append(Paragraph("3. Top 5 Contributors", h1_style))
    donors_data = [[
        Paragraph("<b>Donor Name</b>", table_header_style),
        Paragraph("<b>Email Address</b>", table_header_style),
        Paragraph("<b>Type</b>", table_header_style),
        Paragraph("<b>Total Amount</b>", table_header_style)
    ]]
    for donor in dash_stats['top_donors']:
        donors_data.append([
            Paragraph(donor['name'], table_cell_style),
            Paragraph(donor['email'], table_cell_style),
            Paragraph(donor['type'], table_cell_style),
            Paragraph(f"Rs. {donor['total_amount']:,.2f}", table_cell_style)
        ])
    if not dash_stats['top_donors']:
        donors_data.append([Paragraph("No donor contributions registered", table_cell_style), Paragraph("-", table_cell_style), Paragraph("-", table_cell_style), Paragraph("Rs. 0.00", table_cell_style)])
    
    donors_table = Table(donors_data, colWidths=[130, 164, 90, 120])
    donors_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    story.append(donors_table)
    story.append(Spacer(1, 15))
    
    # Expenses Table (Width: 504 pt)
    story.append(Paragraph("4. Project-wise Operational Expenditures", h1_style))
    expenses_data = [[Paragraph("<b>Project Name</b>", table_header_style), Paragraph("<b>Total Expenditures</b>", table_header_style)]]
    
    for i, label in enumerate(dash_stats['project_expense_labels']):
        amount = dash_stats['project_expense_values'][i]
        expenses_data.append([
            Paragraph(label, table_cell_style),
            Paragraph(f"Rs. {amount:,.2f}", table_cell_style)
        ])
        
    if len(expenses_data) == 1:
        expenses_data.append([Paragraph("No project expense records available", table_cell_style), Paragraph("Rs. 0.00", table_cell_style)])
        
    expenses_table = Table(expenses_data, colWidths=[252, 252])
    expenses_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#334155')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    story.append(expenses_table)
    
    # Page Break to avoid table orphans
    story.append(PageBreak())
    
    # Volunteer Count Table (Width: 504 pt)
    story.append(Paragraph("5. Volunteer Allocation per Branch", h1_style))
    vol_data = [[Paragraph("<b>Branch Name</b>", table_header_style), Paragraph("<b>Active Volunteers Assigned</b>", table_header_style)]]
    
    for item in dash_stats['branch_volunteers']:
        vol_data.append([
            Paragraph(item['branch__name'], table_cell_style),
            Paragraph(str(item['volunteer_count']), table_cell_style)
        ])
        
    if len(vol_data) == 1:
        vol_data.append([Paragraph("No volunteers assigned", table_cell_style), Paragraph("0", table_cell_style)])
        
    vol_table = Table(vol_data, colWidths=[252, 252])
    vol_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#475569')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    story.append(vol_table)
    story.append(Spacer(1, 15))

    # Volunteer Assignments Table (Width: 504 pt)
    story.append(Paragraph("6. Campaign Service Assignments & Volunteer Contributions", h1_style))
    assign_data = [[
        Paragraph("<b>Volunteer</b>", table_header_style),
        Paragraph("<b>Project</b>", table_header_style),
        Paragraph("<b>Role</b>", table_header_style),
        Paragraph("<b>Service Hours</b>", table_header_style),
        Paragraph("<b>Status</b>", table_header_style)
    ]]
    
    assignments_list = VolunteerAssignment.objects.select_related('volunteer', 'project').all()
    for assign in assignments_list:
        assign_data.append([
            Paragraph(assign.volunteer.name, table_cell_style),
            Paragraph(assign.project.name, table_cell_style),
            Paragraph(assign.role, table_cell_style),
            Paragraph(f"{assign.hours_spent} hours", table_cell_style),
            Paragraph(assign.get_status_display(), table_cell_style)
        ])
        
    if not assignments_list:
        assign_data.append([
            Paragraph("No volunteer assignments logged", table_cell_style),
            Paragraph("-", table_cell_style),
            Paragraph("-", table_cell_style),
            Paragraph("0 hours", table_cell_style),
            Paragraph("-", table_cell_style)
        ])
        
    assign_table = Table(assign_data, colWidths=[110, 140, 110, 80, 64])
    assign_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0f766e')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    story.append(assign_table)
    story.append(Spacer(1, 15))

    # Inventory Category Summaries (Width: 504 pt)
    story.append(Paragraph("7. Inventory Category Stock Summary", h1_style))
    inv_data = [[Paragraph("<b>Supply Category</b>", table_header_style), Paragraph("<b>Total Volume / Stock Units</b>", table_header_style)]]
    for i, label in enumerate(dash_stats['inventory_labels']):
        amount = dash_stats['inventory_values'][i]
        inv_data.append([
            Paragraph(label, table_cell_style),
            Paragraph(f"{amount:,.2f}", table_cell_style)
        ])
    if len(inv_data) == 1:
        inv_data.append([Paragraph("No inventory tracked", table_cell_style), Paragraph("0.00", table_cell_style)])
    
    inv_table = Table(inv_data, colWidths=[252, 252])
    inv_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#475569')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')])
    ]))
    story.append(inv_table)
    story.append(Spacer(1, 15))
    
    # Beneficiary Summary
    story.append(Paragraph("7. Community Impact & Beneficiaries Served", h1_style))
    total_beneficiaries = home_stats['total_beneficiaries']
    total_distributions = AidDistribution.objects.aggregate(Sum('quantity'))['quantity__sum'] or 0
    story.append(Paragraph(f"To date, Seva Setu has registered <b>{total_beneficiaries:,}</b> unique individuals in its beneficiary database and completed <b>{total_distributions:,}</b> individual aid distribution sessions (including cooked meals, dry rations, winter clothing, and medical checkups) across all branches.", body_style))
    
    # Build Document using NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)

