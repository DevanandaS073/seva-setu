# Seva Setu – NGO Resource & Donation Management Portal

Seva Setu is a full-stack, enterprise-grade web application designed for NGOs managing community services across multiple locations. Built with Django and PostgreSQL, the portal centralizes donor management, volunteer shift directories, stock inventory audits, beneficiary logging, and financial ledger tracing.

## Features

1. **Donor Directory & Audits**: Log contributions, map corporate and individual donor profiles, and track payment mode histories.
2. **Multi-Branch Resource Allocations**: Track branch details, local manager assignments, and operational locations.
3. **Cross-Branch Inventory Tracking**: Audit medicine, clothing, food, and miscellaneous supplies.
4. **Volunteer Directory**: Assign shifts (morning, afternoon, evening), log volunteer skills, and perform status updates (active/inactive).
5. **Beneficiary Logs**: Log meal servings and headcount metrics per branch.
6. **Expense Tracking**: Track utility, staff salaries, transport, and food costs.
7. **Impact Analytics Dashboard**: Real-time business intelligence using **Pandas** for server-side processing and **Chart.js** for responsive UI charts:
   - Branch donations bar chart
   - Expense category distribution pie chart
   - 6-month donation line trend
   - Inventory category stock allocation doughnut chart
   - Volunteer active status ratio chart
   - Beneficiary meal count logs
8. **Fund Utilization PDF Reports**: Generates confidential, print-ready, dynamic PDF reports utilizing **ReportLab**'s flowable formatting and custom two-pass page numbers (`NumberedCanvas`).

---

## Tech Stack

- **Backend**: Python 3.11/3.13, Django 4.2
- **Database**: PostgreSQL 18
- **Data Analysis**: Pandas
- **Reporting**: ReportLab PDF
- **Frontend**: HTML5, CSS3, Bootstrap 5 (CDN), Chart.js (CDN), Bootstrap Icons

---

## Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL server (running locally on port 5432)

### 1. Clone & Set Up Directory
Navigate to your project directory:
```bash
cd seva_setu
```

### 2. Install Dependencies
Install all python packages via pip:
```bash
pip install -r requirements.txt
```

### 3. Database Initial Setup
Ensure your local PostgreSQL service is running. The project is configured in `settings.py` to connect to:
- **DB Name**: `ngodb`
- **User**: `ngoadmin`
- **Password**: `ngo@1234`

If you need to create this database and role in PostgreSQL, run the following SQL commands:
```sql
CREATE ROLE ngoadmin WITH LOGIN PASSWORD 'ngo@1234' CREATEDB;
CREATE DATABASE ngodb OWNER ngoadmin;
```

### 4. Run Migrations
Run migrations to build database schemas:
```bash
cd ngo_portal
python manage.py makemigrations
python manage.py migrate
```

### 5. Seed Demonstration Data
Seed sample data (3 branches, 5 donors, 10 donations, 15 inventory items, 8 volunteers, 20 beneficiary records, 10 expenses) and generate the default administrator account:
```bash
python manage.py seed
```

### 6. Run Server
Start the local development server:
```bash
python manage.py runserver
```
Visit the portal at `http://127.0.0.1:8000/`.

---

## User Credentials (Demo)

- **Admin Panel Access**: `http://127.0.0.1:8000/admin/`
- **Username**: `admin`
- **Password**: `admin123`
