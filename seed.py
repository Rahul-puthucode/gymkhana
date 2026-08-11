import os
import sqlite3
from datetime import date, timedelta
from werkzeug.security import generate_password_hash
from app import create_app
from utils.database import execute_db, query_db, get_db

def seed_database():
    app = create_app()
    with app.app_context():
        # Ensure schema table structures are initialized
        db = get_db()
        db_driver = getattr(app, 'db_driver', 'sqlite')
        
        # Read schema.sql and create tables if using SQLite fallback or raw connection
        schema_path = os.path.join(app.root_path, 'schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
                
            # If using sqlite fallback, strip MySQL-specific keywords
            if isinstance(db, sqlite3.Connection):
                sqlite_sql = schema_sql.replace('INT AUTO_INCREMENT PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT')
                sqlite_sql = sqlite_sql.replace('AUTO_INCREMENT', '')
                sqlite_sql = sqlite_sql.replace('ENGINE=InnoDB', '')
                sqlite_sql = sqlite_sql.replace('DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP', 'DEFAULT CURRENT_TIMESTAMP')
                sqlite_sql = sqlite_sql.replace('DECIMAL(10, 8)', 'REAL')
                sqlite_sql = sqlite_sql.replace('DECIMAL(11, 8)', 'REAL')
                sqlite_sql = sqlite_sql.replace('DECIMAL(5, 2)', 'REAL')
                sqlite_sql = sqlite_sql.replace('DECIMAL(10, 2)', 'REAL')
                sqlite_sql = sqlite_sql.replace('TINYINT(1)', 'INTEGER')
                
                # Execute statements
                statements = [stmt.strip() for stmt in sqlite_sql.split(';') if stmt.strip()]
                cursor = db.cursor()
                for stmt in statements:
                    if 'CREATE DATABASE' in stmt or 'USE ' in stmt:
                        continue
                    try:
                        cursor.execute(stmt)
                    except Exception as e:
                        pass
                db.commit()

        print("Initializing roles...")
        execute_db("INSERT OR IGNORE INTO roles (id, name) VALUES (1, 'MEMBER')")
        execute_db("INSERT OR IGNORE INTO roles (id, name) VALUES (2, 'TRAINER')")
        execute_db("INSERT OR IGNORE INTO roles (id, name) VALUES (3, 'ADMIN')")

        # 1. Admin User
        admin_pass = generate_password_hash("Admin@123")
        existing_admin = query_db("SELECT id FROM users WHERE email = 'admin@gymkhana.com'", one=True)
        if not existing_admin:
            admin_id = execute_db(
                """INSERT INTO users (role_id, name, email, password_hash, phone, gender, status)
                   VALUES (3, 'System Administrator', 'admin@gymkhana.com', %s, '+91 9999900000', 'Other', 'active')""",
                (admin_pass,)
            )
            print("Seeded Admin: admin@gymkhana.com / Admin@123")

        # 2. Trainers
        trainer_pass = generate_password_hash("Trainer@123")
        trainers_data = [
            ("Alex Mercer", "trainer1@gymkhana.com", "+91 9876511111", "Strength & Conditioning", "6 Years", "CSCS Certified"),
            ("Sarah Jenkins", "trainer2@gymkhana.com", "+91 9876522222", "Weight Loss & Clinical Dietetics", "4 Years", "ACE Fitness Master")
        ]
        
        trainer_user_ids = []
        for name, email, phone, spec, exp, qual in trainers_data:
            t_user = query_db("SELECT id FROM users WHERE email = %s", (email,), one=True)
            if not t_user:
                u_id = execute_db(
                    """INSERT INTO users (role_id, name, email, password_hash, phone, gender, status)
                       VALUES (2, %s, %s, %s, %s, 'Male', 'active')""",
                    (name, email, trainer_pass, phone)
                )
                execute_db(
                    """INSERT INTO trainers (user_id, specialization, experience, qualification, status)
                       VALUES (%s, %s, %s, %s, 'active')""",
                    (u_id, spec, exp, qual)
                )
                trainer_user_ids.append(u_id)
                print(f"Seeded Trainer: {email} / Trainer@123")
            else:
                trainer_user_ids.append(t_user['id'])

        # 3. Members
        member_pass = generate_password_hash("Member@123")
        members_data = [
            ("Rahul Sharma", "member1@gymkhana.com", "+91 9876533333", "Male", "1998-05-15", 176.0, 78.5),
            ("Anita Roy", "member2@gymkhana.com", "+91 9876544444", "Female", "1999-08-20", 162.0, 58.0),
            ("Vikram Patel", "member3@gymkhana.com", "+91 9876555555", "Male", "1995-11-10", 180.0, 85.0),
            ("Priya Nair", "member4@gymkhana.com", "+91 9876566666", "Female", "2000-02-28", 165.0, 62.5),
            ("Karan Verma", "member5@gymkhana.com", "+91 9876577777", "Male", "1997-09-04", 172.0, 72.0)
        ]

        member_ids = []
        for name, email, phone, gender, dob, height, weight in members_data:
            m_user = query_db("SELECT id FROM users WHERE email = %s", (email,), one=True)
            if not m_user:
                m_id = execute_db(
                    """INSERT INTO users (role_id, name, email, password_hash, phone, gender, date_of_birth, height, weight, status)
                       VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, 'active')""",
                    (name, email, member_pass, phone, gender, dob, height, weight)
                )
                member_ids.append(m_id)
                print(f"Seeded Member: {email} / Member@123")
                
                # Seed Initial Fitness Progress for members
                bmi = round(weight / ((height / 100.0) ** 2), 2)
                execute_db(
                    """INSERT INTO fitness_progress (member_id, weight, height, bmi, chest, waist, arms, thighs, recorded_at)
                       VALUES (%s, %s, %s, %s, 98.0, 82.0, 34.0, 54.0, %s)""",
                    (m_id, weight, height, bmi, date.today() - timedelta(days=30))
                )
                execute_db(
                    """INSERT INTO fitness_progress (member_id, weight, height, bmi, chest, waist, arms, thighs, recorded_at)
                       VALUES (%s, %s, %s, %s, 97.0, 81.0, 34.5, 53.5, %s)""",
                    (m_id, weight - 1.2, height, round((weight - 1.2) / ((height / 100.0) ** 2), 2), date.today())
                )
            else:
                member_ids.append(m_user['id'])

        # 4. Membership Plans
        plans_data = [
            ("Monthly Pass", "Standard monthly membership with full access to gym floor and lockers.", 1, 1500.0, "Gym Floor Access\nLocker Room & Showers\nFree Fitness Assessment"),
            ("Quarterly Pass", "Popular 3-month package with complimentary personal trainer orientation.", 3, 4000.0, "Gym Floor Access\nLocker Room & Showers\n1 Trainer Session/Month\nDiet Plan Consultation"),
            ("Half-Yearly Pass", "6-month transformation program with nutrition and workout tracking.", 6, 7500.0, "All Standard Benefits\nDedicated Trainer Support\nMonthly Body Analysis\n10% Supplement Discount"),
            ("Yearly VIP Pass", "Ultimate 12-month all-access pass with premium perks.", 12, 13000.0, "All Access Nationwide\nPersonalized Trainer & Diet Plan\nFree Gymkhana T-Shirt & Towel\n24/7 VIP Access")
        ]

        plan_ids = []
        for name, desc, duration, price, benefits in plans_data:
            ex_plan = query_db("SELECT id FROM membership_plans WHERE name = %s", (name,), one=True)
            if not ex_plan:
                p_id = execute_db(
                    """INSERT INTO membership_plans (name, description, duration_months, price, benefits, status)
                       VALUES (%s, %s, %s, %s, %s, 'active')""",
                    (name, desc, duration, price, benefits)
                )
                plan_ids.append(p_id)
            else:
                plan_ids.append(ex_plan['id'])

        print("Seeded 4 Membership Plans.")

        # 5. Subscriptions
        if member_ids and plan_ids:
            for idx, m_id in enumerate(member_ids[:3]):
                ex_sub = query_db("SELECT id FROM subscriptions WHERE member_id = %s", (m_id,), one=True)
                if not ex_sub:
                    plan_id = plan_ids[idx % len(plan_ids)]
                    sub_id = execute_db(
                        """INSERT INTO subscriptions (member_id, plan_id, start_date, expiry_date, amount, status)
                           VALUES (%s, %s, %s, %s, %s, 'active')""",
                        (m_id, plan_id, date.today() - timedelta(days=10), date.today() + timedelta(days=80), 4000.0)
                    )
                    execute_db(
                        """INSERT INTO subscription_history (subscription_id, member_id, plan_id, action, amount)
                           VALUES (%s, %s, %s, 'SUBSCRIBE', 4000.0)""",
                        (sub_id, m_id, plan_id)
                    )

        # 6. Gym Branches
        branches_data = [
            ("Gymkhana Fitness — Palakkad Central", "Near Stadium Bypass Road, Palakkad, Kerala 678001", "+91 9876500001", "06:00 AM - 10:00 PM", "Cardio Zone, Heavy Weight Floor, Sauna, Cafe", 10.7867, 76.6548),
            ("Gymkhana Fitness — Coimbatore Hub", "Avinashi Road, Peelamedu, Coimbatore, Tamil Nadu 641004", "+91 9876500002", "05:30 AM - 10:30 PM", "CrossFit Arena, Steam Bath, Personal Training Studio", 11.0168, 76.9558),
            ("Gymkhana Fitness — Kochi Metro", "MG Road, Ernakulam, Kochi, Kerala 682016", "+91 9876500003", "06:00 AM - 10:00 PM", "Full Body Circuit, Juice Bar, Lockers & Showers", 9.9312, 76.2673)
        ]

        for b_name, addr, phone, hrs, fac, lat, lng in branches_data:
            ex_b = query_db("SELECT id FROM gym_branches WHERE name = %s", (b_name,), one=True)
            if not ex_b:
                execute_db(
                    """INSERT INTO gym_branches (name, address, phone, opening_hours, facilities, latitude, longitude, status)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, 'active')""",
                    (b_name, addr, phone, hrs, fac, lat, lng)
                )

        print("Seeded 3 Gym Branch Locations.")

        # 7. Exercises (15 Exercises)
        exercises_data = [
            ("Bench Press", "Chest", "Barbell", "Lie on bench, grip bar slightly wider than shoulder width, lower bar to chest level and press up Explosively.", "Core compound movement for pectoral strength."),
            ("Incline Dumbbell Press", "Chest", "Dumbbells", "Set bench to 30 degrees, press dumbbells overhead concentrating on upper chest contraction.", "Targets upper chest fibers."),
            ("Cable Fly", "Chest", "Cable Machine", "Stand in center of cable pulleys, pull handles in sweeping arc until hands meet in front.", "Isolates chest with constant cable tension."),
            ("Squat", "Legs", "Barbell", "Place bar across upper back, squat down keeping knees aligned over toes until thighs are parallel to ground.", "King of lower body compound exercises."),
            ("Leg Press", "Legs", "Leg Press Machine", "Place feet shoulder-width apart on sled, push platform up until legs are extended.", "Builds quadriceps strength safely."),
            ("Leg Curl", "Legs", "Lying Leg Curl Machine", "Lie face down, curl weight towards glutes emphasizing hamstring contraction.", "Targets hamstring muscle group."),
            ("Deadlift", "Back", "Barbell", "Hinge at hips with flat back, grip bar, and stand up driving through heels.", "Full-body posterior chain power exercise."),
            ("Lat Pulldown", "Back", "Cable Pulldown", "Grip wide bar, pull bar down smoothly to upper chest retracting shoulder blades.", "Develops upper back latissimus dorsi width."),
            ("Seated Cable Row", "Back", "Cable Row", "Sit with upright torso, pull cable attachment towards abdomen squeezing mid-back.", "Targets mid-back thickness."),
            ("Overhead Shoulder Press", "Shoulders", "Dumbbells", "Press dumbbells vertically overhead from shoulder level without arching lower back.", "Builds deltoids and shoulder stability."),
            ("Lateral Raise", "Shoulders", "Dumbbells", "Raise dumbbells laterally out to sides until parallel to floor with slight elbow bend.", "Isolates lateral side deltoids."),
            ("Bicep Curl", "Arms", "Barbell", "Keep elbows tucked into sides, curl bar upwards contracting biceps.", "Classic arm hypertrophy movement."),
            ("Triceps Pushdown", "Arms", "Cable Machine", "Attach rope to high pulley, push rope down extending elbows fully at bottom.", "Isolates triceps brachii."),
            ("Plank", "Core", "Bodyweight", "Maintain rigid pushup position supported on forearms for target duration.", "Core stability isometric exercise."),
            ("Abdominal Crunch", "Core", "Bodyweight", "Lie back on mat, flex abs to curl shoulders towards knees.", "Isolates rectus abdominis.")
        ]

        ex_map = {}
        for ex_name, muscle, equip, inst, desc in exercises_data:
            ex_rec = query_db("SELECT id FROM exercises WHERE name = %s", (ex_name,), one=True)
            if not ex_rec:
                e_id = execute_db(
                    """INSERT INTO exercises (name, muscle_group, equipment, instructions, description)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (ex_name, muscle, equip, inst, desc)
                )
                ex_map[ex_name] = e_id
            else:
                ex_map[ex_name] = ex_rec['id']

        print("Seeded 15 Exercises.")

        # 8. Sample Workout Plan for Member 1
        if member_ids and trainer_user_ids:
            m1_id = member_ids[0]
            t1_id = trainer_user_ids[0]
            
            ex_plan = query_db("SELECT id FROM workout_plans WHERE member_id = %s", (m1_id,), one=True)
            if not ex_plan:
                wp_id = execute_db(
                    """INSERT INTO workout_plans (member_id, trainer_id, name, description, start_date, end_date, status)
                       VALUES (%s, %s, 'Hypertrophy & Strength Program', '4-day split program focusing on progressive overload.', %s, %s, 'active')""",
                    (m1_id, t1_id, date.today() - timedelta(days=5), date.today() + timedelta(days=30))
                )

                workout_items = [
                    ("Day 1 - Chest & Triceps", ex_map.get("Bench Press"), 4, "8-10", "60 kg", 90),
                    ("Day 1 - Chest & Triceps", ex_map.get("Incline Dumbbell Press"), 3, "10", "22 kg", 60),
                    ("Day 1 - Chest & Triceps", ex_map.get("Triceps Pushdown"), 3, "12", "25 kg", 60),
                    ("Day 2 - Back & Biceps", ex_map.get("Deadlift"), 4, "6", "100 kg", 120),
                    ("Day 2 - Back & Biceps", ex_map.get("Lat Pulldown"), 3, "10", "50 kg", 60),
                    ("Day 2 - Back & Biceps", ex_map.get("Bicep Curl"), 3, "12", "15 kg", 60),
                    ("Day 3 - Legs & Core", ex_map.get("Squat"), 4, "8", "80 kg", 90),
                    ("Day 3 - Legs & Core", ex_map.get("Leg Press"), 3, "10", "140 kg", 60),
                    ("Day 3 - Legs & Core", ex_map.get("Plank"), 3, "60 sec", "Bodyweight", 45)
                ]

                for day, exercise_id, sets, reps, weight, rest in workout_items:
                    if exercise_id:
                        execute_db(
                            """INSERT INTO workout_exercises (workout_plan_id, exercise_id, day, sets, reps, weight, rest_seconds)
                               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                            (wp_id, exercise_id, day, sets, reps, weight, rest)
                        )
                print("Seeded Sample Workout Plan.")

        # 9. Sample Diet Plan for Member 1
        if member_ids and trainer_user_ids:
            m1_id = member_ids[0]
            t1_id = trainer_user_ids[0]
            
            ex_dp = query_db("SELECT id FROM diet_plans WHERE member_id = %s", (m1_id,), one=True)
            if not ex_dp:
                dp_id = execute_db(
                    """INSERT INTO diet_plans (member_id, trainer_id, name, goal, calories, protein, carbohydrates, fat, start_date, end_date, status)
                       VALUES (%s, %s, 'Lean Muscle Building Diet', 'Build lean mass with 2,400 kcal daily intake.', 2400, 160, 260, 65, %s, %s, 'active')""",
                    (m1_id, t1_id, date.today() - timedelta(days=5), date.today() + timedelta(days=30))
                )

                meals = [
                    ("Breakfast", "Oatmeal with Almond Milk & Protein Powder", "1 Bowl (350g)", 450, 32, 55, 8, "Add 1 sliced banana"),
                    ("Mid-morning", "Boiled Whole Eggs & Green Tea", "3 Eggs", 210, 18, 2, 14, "Sprinkle black pepper"),
                    ("Lunch", "Grilled Chicken Breast with Brown Rice & Broccoli", "200g Chicken + 150g Rice", 650, 48, 65, 12, "Drizzle olive oil"),
                    ("Evening snack", "Greek Yogurt with Mixed Berries", "200g", 200, 15, 20, 4, "High protein snack"),
                    ("Dinner", "Paneer / Fish Tikka with Wheat Roti & Salad", "150g Paneer + 2 Rotis", 550, 35, 45, 20, "Eat before 9 PM")
                ]

                for mtype, food, qty, cals, prot, carbs, fat, notes in meals:
                    execute_db(
                        """INSERT INTO diet_meals (diet_plan_id, meal_type, food_name, quantity, calories, protein, carbohydrates, fat, notes)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (dp_id, mtype, food, qty, cals, prot, carbs, fat, notes)
                    )
                print("Seeded Sample Diet Plan.")

        # 10. Sample Notifications
        if member_ids:
            for m_id in member_ids:
                execute_db(
                    """INSERT INTO notifications (user_id, title, message, type, is_read)
                       VALUES (%s, 'Welcome to Gymkhana!', 'Explore your personal dashboard to track workout and diet plans.', 'info', 0)""",
                    (m_id,)
                )

        print("DB Seeding Complete Successfully!")

if __name__ == '__main__':
    seed_database()
