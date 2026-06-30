import datetime
import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Branch, Donor, Donation, InventoryItem, Volunteer, Beneficiary, Expense, FundAllocation, AidDistribution, InventoryTransaction, Project, VolunteerAssignment

class Command(BaseCommand):
    help = 'Seeds the database with sample data for demonstration'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Clearing existing database records..."))
        
        # Delete old records
        InventoryTransaction.objects.all().delete()
        AidDistribution.objects.all().delete()
        FundAllocation.objects.all().delete()
        Expense.objects.all().delete()
        Project.objects.all().delete()
        Beneficiary.objects.all().delete()
        Volunteer.objects.all().delete()
        InventoryItem.objects.all().delete()
        Donation.objects.all().delete()
        Donor.objects.all().delete()
        Branch.objects.all().delete()

        self.stdout.write("Database cleared. Seeding new sample data...")

        # 1. Create Branches (3 branches)
        branches_data = [
            {"name": "Mumbai Central Branch", "location": "Fort, Mumbai, Maharashtra", "manager_name": "Rajesh Mehta", "phone": "022-22615432"},
            {"name": "Delhi North Branch", "location": "Connaught Place, New Delhi", "manager_name": "Priyanka Singh", "phone": "011-43516543"},
            {"name": "Kolkata East Branch", "location": "Salt Lake, Kolkata, West Bengal", "manager_name": "Subir Sen", "phone": "033-23348765"},
        ]
        branches = []
        for b_data in branches_data:
            branch = Branch.objects.create(**b_data)
            branches.append(branch)
            self.stdout.write(f"Created Branch: {branch.name}")

        # 2. Create Donors (5 donors)
        donors_data = [
            {"name": "Rohan Sharma", "email": "rohan@gmail.com", "phone": "9820012345", "address": "Bandra, Mumbai", "donor_type": "individual", "username": "rohan"},
            {"name": "Sneha Patel", "email": "sneha@yahoo.com", "phone": "9819923456", "address": "Andheri, Mumbai", "donor_type": "individual", "username": "sneha"},
            {"name": "Tech Solutions Corp", "email": "csr@techcorp.com", "phone": "022-67891234", "address": "BKC, Mumbai", "donor_type": "corporate", "username": "techcorp"},
            {"name": "Global Trust Foundation", "email": "grants@globaltrust.org", "phone": "011-25674321", "address": "Vasant Kunj, Delhi", "donor_type": "corporate", "username": "globaltrust"},
            {"name": "Amit Verma", "email": "amit.verma@hotmail.com", "phone": "9899012345", "address": "Dwarka, Delhi", "donor_type": "individual", "username": "amit"},
        ]
        donors = []
        for d_data in donors_data:
            username = d_data.pop("username")
            user = User.objects.create_user(username=username, email=d_data["email"], password="password123")
            donor = Donor.objects.create(user=user, **d_data)
            donors.append(donor)
            self.stdout.write(f"Created Donor: {donor.name} (User: {username}, Password: password123)")

        # 3. Create Donations (10 donations spread across last 6 months)
        now = timezone.now().date()
        donations_meta = [
            {"donor": donors[0], "branch": branches[0], "amount": 5000.00, "days_ago": 10, "mode": "online", "notes": "General branch support"},
            {"donor": donors[1], "branch": branches[0], "amount": 3500.00, "days_ago": 35, "mode": "cash", "notes": "Food drive funding"},
            {"donor": donors[2], "branch": branches[1], "amount": 50000.00, "days_ago": 60, "mode": "cheque", "notes": "Corporate CSR contribution"},
            {"donor": donors[3], "branch": branches[2], "amount": 75000.00, "days_ago": 95, "mode": "online", "notes": "Quarterly branch grant"},
            {"donor": donors[4], "branch": branches[1], "amount": 10000.00, "days_ago": 120, "mode": "online", "notes": "Educational aids donation"},
            {"donor": donors[0], "branch": branches[2], "amount": 8000.00, "days_ago": 140, "mode": "cheque", "notes": "Medical supplies funding"},
            {"donor": donors[1], "branch": branches[1], "amount": 4000.00, "days_ago": 155, "mode": "cash", "notes": "Winter clothing drive"},
            {"donor": donors[2], "branch": branches[0], "amount": 25000.00, "days_ago": 170, "mode": "online", "notes": "Tech infrastructure donation"},
            {"donor": donors[3], "branch": branches[0], "amount": 60000.00, "days_ago": 180, "mode": "cheque", "notes": "Initiation branch grant"},
            {"donor": donors[4], "branch": branches[2], "amount": 12000.00, "days_ago": 20, "mode": "online", "notes": "Monsoon relief funds"},
        ]
        for d_meta in donations_meta:
            donation = Donation.objects.create(
                donor=d_meta["donor"],
                amount=d_meta["amount"],
                date=now - datetime.timedelta(days=d_meta["days_ago"]),
                payment_mode=d_meta["mode"],
                notes=d_meta["notes"]
            )
            FundAllocation.objects.create(
                donation=donation,
                branch=d_meta["branch"],
                amount=d_meta["amount"],
                date=donation.date,
                notes="Auto-allocated from seed donation"
            )
            self.stdout.write(f"Logged Donation: Rs. {donation.amount} on {donation.date} (Allocated to {d_meta['branch'].name})")

        # 3b. Create Item/In-Kind Donations (5 donations)
        item_donations_meta = [
            {"donor": donors[0], "branch": branches[0], "category": "clothing", "name": "Winter Sweaters", "qty": 40.00, "unit": "pieces", "days_ago": 15, "notes": "Winter wear clothing drive donation"},
            {"donor": donors[1], "branch": branches[0], "category": "food", "name": "Basmati Rice", "qty": 150.00, "unit": "kg", "days_ago": 25, "notes": "Dry groceries supply"},
            {"donor": donors[2], "branch": branches[1], "category": "medicine", "name": "Paracetamol Tablets", "qty": 500.00, "unit": "pieces", "days_ago": 40, "notes": "Essential medical aid donation"},
            {"donor": donors[3], "branch": branches[2], "category": "clothing", "name": "Sarees & Dhotis", "qty": 100.00, "unit": "pieces", "days_ago": 80, "notes": "Festival clothing distribution drive"},
            {"donor": donors[4], "branch": branches[1], "category": "other", "name": "Notebooks", "qty": 200.00, "unit": "pieces", "days_ago": 5, "notes": "School books and writing materials"}
        ]
        for item_d in item_donations_meta:
            donation = Donation.objects.create(
                donor=item_d["donor"],
                donation_type="item",
                item_category=item_d["category"],
                item_name=item_d["name"],
                item_quantity=item_d["qty"],
                item_unit=item_d["unit"],
                target_branch=item_d["branch"],
                date=now - datetime.timedelta(days=item_d["days_ago"]),
                notes=item_d["notes"]
            )
            self.stdout.write(f"Logged In-Kind Donation: {donation.item_quantity} {donation.item_unit} of {donation.item_name} on {donation.date} (Target: {donation.target_branch.name})")

        # 4. Create Inventory Items (15 items across branches)
        inventory_items_data = [
            # Mumbai Branch Items
            {"name": "Basmati Rice", "category": "food", "branch": branches[0], "quantity": 350.50, "unit": "kg"},
            {"name": "Wheat Flour", "category": "food", "branch": branches[0], "quantity": 400.00, "unit": "kg"},
            {"name": "Paracetamol Tablets", "category": "medicine", "branch": branches[0], "quantity": 1200.00, "unit": "pieces"},
            {"name": "Blankets", "category": "clothing", "branch": branches[0], "quantity": 80.00, "unit": "pieces"},
            {"name": "Winter Sweaters", "category": "clothing", "branch": branches[0], "quantity": 50.00, "unit": "pieces"},
            # Delhi Branch Items
            {"name": "Cooking Oil", "category": "food", "branch": branches[1], "quantity": 180.00, "unit": "litres"},
            {"name": "Cough Syrup", "category": "medicine", "branch": branches[1], "quantity": 150.00, "unit": "litres"},
            {"name": "Kids School Bags", "category": "other", "branch": branches[1], "quantity": 110.00, "unit": "pieces"},
            {"name": "T-Shirts", "category": "clothing", "branch": branches[1], "quantity": 300.00, "unit": "pieces"},
            {"name": "Notebooks", "category": "other", "branch": branches[1], "quantity": 500.00, "unit": "pieces"},
            # Kolkata Branch Items
            {"name": "Red Lentils (Masoor Dal)", "category": "food", "branch": branches[2], "quantity": 250.00, "unit": "kg"},
            {"name": "First Aid Kits", "category": "medicine", "branch": branches[2], "quantity": 45.00, "unit": "pieces"},
            {"name": "Sarees & Dhotis", "category": "clothing", "branch": branches[2], "quantity": 150.00, "unit": "pieces"},
            {"name": "Anti-septic Solution", "category": "medicine", "branch": branches[2], "quantity": 90.00, "unit": "litres"},
            {"name": "Sanitary Pads", "category": "other", "branch": branches[2], "quantity": 800.00, "unit": "pieces"},
        ]
        for inv_data in inventory_items_data:
            qty = inv_data.pop("quantity")
            item, created = InventoryItem.objects.get_or_create(
                branch=inv_data["branch"],
                name=inv_data["name"],
                category=inv_data["category"],
                defaults={"unit": inv_data["unit"]}
            )
            # Log Stock In
            InventoryTransaction.objects.create(
                item=item,
                transaction_type="in",
                quantity=qty,
                date=timezone.now() - datetime.timedelta(days=random.randint(20, 60)),
                notes="Initial seeder stock ingestion."
            )
            # Log Stock Out (distribution)
            if qty > 50:
                out_qty = random.randint(10, 40)
                InventoryTransaction.objects.create(
                    item=item,
                    transaction_type="out",
                    quantity=out_qty,
                    date=timezone.now() - datetime.timedelta(days=random.randint(1, 19)),
                    notes="Distributed to local beneficiaries."
                )
            self.stdout.write(f"Added Inventory Item: {item.name} at {item.branch.name} (Calculated Stock: {item.quantity} {item.unit})")

        # 5. Create Volunteers (8 volunteers)
        volunteers_data = [
            {"name": "Karan Malhotra", "email": "karan@example.com", "phone": "9910012345", "branch": branches[0], "skill": "Teaching / Mentoring", "shift": "morning", "is_active": True},
            {"name": "Neha Joshi", "email": "neha@example.com", "phone": "9812233445", "branch": branches[0], "skill": "Food Preparation", "shift": "afternoon", "is_active": True},
            {"name": "Aditya Roy", "email": "aditya@example.com", "phone": "9933445566", "branch": branches[0], "skill": "Medical Assistance", "shift": "evening", "is_active": False},
            {"name": "Meera Sen", "email": "meera@example.com", "phone": "9876543210", "branch": branches[1], "skill": "Event Management", "shift": "morning", "is_active": True},
            {"name": "Rahul Bose", "email": "rahul@example.com", "phone": "9830023456", "branch": branches[2], "skill": "First Aid / Relief Work", "shift": "evening", "is_active": True},
            {"name": "Sonia Gandhi", "email": "sonia@example.com", "phone": "9988776655", "branch": branches[1], "skill": "Social Media & Tech Support", "shift": "afternoon", "is_active": True},
            {"name": "Vikram Rathore", "email": "vikram@example.com", "phone": "9922883377", "branch": branches[2], "skill": "Warehouse logistics", "shift": "morning", "is_active": True},
            {"name": "Pooja Hegde", "email": "pooja@example.com", "phone": "9899123456", "branch": branches[1], "skill": "Teaching", "shift": "evening", "is_active": False},
        ]
        volunteers = []
        for v_data in volunteers_data:
            volunteer = Volunteer.objects.create(**v_data)
            volunteers.append(volunteer)
            self.stdout.write(f"Registered Volunteer: {volunteer.name} ({volunteer.branch.name})")

        # 6. Create Beneficiaries (10 unique profiles)
        beneficiaries_data = [
            {"name": "Aarav Patel", "email": "aarav.patel@gmail.com", "phone": "9812345678", "registered_branch": branches[0]},
            {"name": "Aditi Sharma", "email": "aditi.sharma@yahoo.com", "phone": "9823456789", "registered_branch": branches[0]},
            {"name": "Vihaan Gupta", "email": "vihaan@hotmail.com", "phone": "9834567890", "registered_branch": branches[1]},
            {"name": "Ananya Iyer", "email": "ananya.iyer@gmail.com", "phone": "9845678901", "registered_branch": branches[1]},
            {"name": "Sai Kumar", "email": "sai.kumar@gmail.com", "phone": "9856789012", "registered_branch": branches[2]},
            {"name": "Riya Sen", "email": "riya.sen@yahoo.com", "phone": "9867890123", "registered_branch": branches[2]},
            {"name": "Kabir Singh", "email": "kabir@gmail.com", "phone": "9876543210", "registered_branch": branches[0]},
            {"name": "Diya Bose", "email": "diya.bose@gmail.com", "phone": "9887654321", "registered_branch": branches[2]},
            {"name": "Ishaan Das", "email": "ishaan@yahoo.com", "phone": "9898765432", "registered_branch": branches[1]},
            {"name": "Pooja Reddy", "email": "pooja.reddy@gmail.com", "phone": "9909876543", "registered_branch": branches[2]},
        ]
        beneficiaries = []
        for b_data in beneficiaries_data:
            beneficiary = Beneficiary.objects.create(
                name=b_data["name"],
                email=b_data["email"],
                phone=b_data["phone"],
                registered_branch=b_data["registered_branch"],
                registered_date=now - datetime.timedelta(days=random.randint(10, 150))
            )
            beneficiaries.append(beneficiary)
            self.stdout.write(f"Registered Beneficiary Profile: {beneficiary.name}")

        # 6b. Create Aid Distributions (20 distribution records linked to branch inventory)
        aid_types = ["meal", "medicine", "clothing", "other"]
        meal_types = ["breakfast", "lunch", "dinner"]
        
        # Map aid_type to InventoryItem category
        category_map = {
            "meal": "food",
            "medicine": "medicine",
            "clothing": "clothing",
            "other": "other"
        }
        
        for i in range(20):
            beneficiary = random.choice(beneficiaries)
            branch = random.choice(branches)
            date = now - datetime.timedelta(days=random.randint(1, 150))
            aid_type = random.choice(aid_types)
            quantity = random.randint(1, 5)
            
            # Find a matching inventory item in the same branch that has available stock
            category = category_map[aid_type]
            items_available = InventoryItem.objects.filter(branch=branch, category=category, quantity__gt=quantity)
            
            inventory_item = None
            if items_available.exists():
                inventory_item = random.choice(list(items_available))
            
            meal_type = None
            if aid_type == "meal":
                meal_type = random.choice(meal_types)
                notes = f"Distributed cooked hot meals to beneficiary."
            elif aid_type == "medicine":
                notes = f"Distributed essential medicine packets."
            elif aid_type == "clothing":
                notes = f"Distributed winter blanket / sweater sets."
            else:
                notes = f"Distributed general assistance items."

            if inventory_item:
                notes += f" Allocated from inventory: {inventory_item.name}."

            AidDistribution.objects.create(
                beneficiary=beneficiary,
                branch=branch,
                inventory_item=inventory_item,
                date=date,
                aid_type=aid_type,
                meal_type=meal_type,
                quantity=quantity,
                notes=notes
            )
        self.stdout.write("Logged 20 Aid Distribution records in ledger.")

        # 7. Create Projects (4 projects)
        project_names = [
            {"name": "Flood Relief Drive", "description": "Emergency food, medicine, and blanket distribution to flood-affected coastal areas.", "days_ago": 120},
            {"name": "Blood Donation Camp", "description": "State-wide voluntary blood donation camp in association with local government hospitals.", "days_ago": 90},
            {"name": "Primary Education Program", "description": "Funding free textbooks, bags, and writing materials for underprivileged school kids.", "days_ago": 150},
            {"name": "Winter Blanket Distribution", "description": "Distributing warm clothing and blankets to homeless street citizens during peak winter months.", "days_ago": 60},
        ]
        projects = []
        for p_meta in project_names:
            project = Project.objects.create(
                name=p_meta["name"],
                description=p_meta["description"],
                start_date=now - datetime.timedelta(days=p_meta["days_ago"]),
                is_active=True
            )
            projects.append(project)
            self.stdout.write(f"Created Project: {project.name}")

        # 8. Create Expenses (10 expenses linked to projects)
        expenses_meta = [
            {"branch": branches[0], "category": "food", "amount": 1200.00, "days_ago": 12, "desc": "Rice and grocery supplies purchase", "rec": "REC-MUM-4561"},
            {"branch": branches[0], "category": "utilities", "amount": 850.00, "days_ago": 30, "desc": "Branch electricity and water bills", "rec": "REC-MUM-4589"},
            {"branch": branches[1], "category": "staff", "amount": 4500.00, "days_ago": 28, "desc": "Field staff monthly stipend", "rec": "REC-DEL-8971"},
            {"branch": branches[1], "category": "transport", "amount": 1500.00, "days_ago": 15, "desc": "Supply distribution truck rent", "rec": "REC-DEL-8999"},
            {"branch": branches[2], "category": "food", "amount": 2200.00, "days_ago": 5, "desc": "Lentils and groceries for feeding program", "rec": "REC-KOL-1200"},
            {"branch": branches[2], "category": "other", "amount": 650.00, "days_ago": 45, "desc": "First aid medicine boxes print and box kits", "rec": "REC-KOL-1223"},
            {"branch": branches[0], "category": "transport", "amount": 1100.00, "days_ago": 75, "desc": "Volunteer bus transportation for medical camp", "rec": "REC-MUM-4322"},
            {"branch": branches[1], "category": "utilities", "amount": 950.00, "days_ago": 90, "desc": "Office internet and utilities", "rec": "REC-DEL-8871"},
            {"branch": branches[2], "category": "staff", "amount": 3000.00, "days_ago": 60, "desc": "Kolkata coordinator stipend", "rec": "REC-KOL-1105"},
            {"branch": branches[0], "category": "food", "amount": 2500.00, "days_ago": 110, "desc": "Bulk purchase of dry food packages", "rec": "REC-MUM-4122"},
        ]
        for e_meta in expenses_meta:
            expense = Expense.objects.create(
                project=random.choice(projects),
                branch=e_meta["branch"],
                category=e_meta["category"],
                amount=e_meta["amount"],
                date=now - datetime.timedelta(days=e_meta["days_ago"]),
                description=e_meta["desc"],
                receipt_number=e_meta["rec"]
            )
            self.stdout.write(f"Logged Expense: Rs. {expense.amount} on {expense.date} for {expense.project.name} (Receipt: {expense.receipt_number})")

        # 9. Create Volunteer Assignments (mapping volunteers to projects)
        assignment_roles = ["Coordinator", "Logistics Lead", "Medic Support", "Meal Server", "Distributor", "Tech Coordinator", "Publicity Lead"]
        for volunteer in volunteers:
            # Assign each volunteer to 1-2 random projects
            assigned_projects = random.sample(projects, k=random.randint(1, 2))
            for project in assigned_projects:
                hours = random.randint(10, 50)
                status = random.choice(['active', 'completed'])
                assignment = VolunteerAssignment.objects.create(
                    volunteer=volunteer,
                    project=project,
                    role=random.choice(assignment_roles),
                    date_assigned=project.start_date + datetime.timedelta(days=random.randint(1, 10)),
                    hours_spent=hours,
                    status=status
                )
                self.stdout.write(f"Logged Volunteer Assignment: {assignment.volunteer.name} assigned to {assignment.project.name} as {assignment.role} ({assignment.hours_spent} hours)")

        # 10. Create Superuser (admin / admin123)
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write(self.style.SUCCESS("Superuser created successfully! Username: admin, Password: admin123"))
        else:
            self.stdout.write("Superuser 'admin' already exists.")

        self.stdout.write(self.style.SUCCESS("Database seeded successfully with all required NGO records!"))
