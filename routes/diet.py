from flask import Blueprint, render_template, session
from utils.database import query_db
from utils.auth import login_required, role_required

diet_bp = Blueprint('diet', __name__, url_prefix='/diet')

@diet_bp.route('/my-diet')
@login_required
@role_required('MEMBER')
def my_diet():
    member_id = session.get('user_id')
    
    plan = query_db(
        """SELECT dp.*, u.name as trainer_name 
           FROM diet_plans dp 
           JOIN users u ON dp.trainer_id = u.id 
           WHERE dp.member_id = %s AND dp.status = 'active' 
           ORDER BY dp.id DESC LIMIT 1""",
        (member_id,), one=True
    )
    
    meals_by_type = {
        'Breakfast': [],
        'Mid-morning': [],
        'Lunch': [],
        'Evening snack': [],
        'Dinner': []
    }
    
    total_calc_calories = 0
    total_calc_protein = 0
    total_calc_carbs = 0
    total_calc_fat = 0
    
    if plan:
        meals = query_db("SELECT * FROM diet_meals WHERE diet_plan_id = %s ORDER BY id ASC", (plan['id'],))
        for meal in meals:
            mtype = meal['meal_type']
            if mtype in meals_by_type:
                meals_by_type[mtype].append(meal)
            else:
                meals_by_type[mtype] = [meal]
                
            total_calc_calories += meal.get('calories', 0)
            total_calc_protein += meal.get('protein', 0)
            total_calc_carbs += meal.get('carbohydrates', 0)
            total_calc_fat += meal.get('fat', 0)

    return render_template(
        'member/diet.html',
        plan=plan,
        meals_by_type=meals_by_type,
        total_calc_calories=total_calc_calories,
        total_calc_protein=total_calc_protein,
        total_calc_carbs=total_calc_carbs,
        total_calc_fat=total_calc_fat
    )
