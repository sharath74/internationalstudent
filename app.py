from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta

import os

app = Flask(__name__)

# Secret key for session
app.secret_key = 'your_secret_key_here'  # Replace with your own strong key!

# SQLite database setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class UniversityApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    university_name = db.Column(db.String(150))
    program_name = db.Column(db.String(150))
    status = db.Column(db.String(50))  # Accepted, Rejected, Pending
    is_final_choice = db.Column(db.Boolean, default=False)

class SubjectGrade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    semester = db.Column(db.String(20))
    subject = db.Column(db.String(100))
    grade = db.Column(db.String(10))

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))


# Route: Home redirects to login
@app.route('/')
def home():
    return redirect(url_for('login'))


# Route: Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        plain_password = request.form['password']

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please login.", "danger")
            return redirect(url_for('register'))

        # Hash password and save
        hashed_password = bcrypt.generate_password_hash(plain_password).decode('utf-8')
        new_user = User(name=name, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registered successfully! You can now login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


# Route: Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        entered_password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("Email not registered. Please register first.", "warning")
            return redirect(url_for('login'))

        if bcrypt.check_password_hash(user.password, entered_password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash("Login successful!", "success")
            return redirect(url_for('university_tracker'))

        else:
            flash("Incorrect password. Try again.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/university-tracker', methods=['GET', 'POST'])
def university_tracker():
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        university = request.form['university']
        program = request.form['program']
        status = request.form['status']
        is_final = 'final_choice' in request.form

        if is_final:
            # Reset previous final choice
            UniversityApplication.query.filter_by(user_id=user_id).update({'is_final_choice': False})

        new_entry = UniversityApplication(
            user_id=user_id,
            university_name=university,
            program_name=program,
            status=status,
            is_final_choice=is_final
        )
        db.session.add(new_entry)
        db.session.commit()
        flash("Application added!", "success")
        return redirect(url_for('university_tracker'))

    applications = UniversityApplication.query.filter_by(user_id=user_id).all()
    return render_template('university_tracker.html', applications=applications)

@app.route('/mark-final/<int:app_id>', methods=['POST'])
def mark_final(app_id):
    if 'user_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    selected_app = UniversityApplication.query.filter_by(id=app_id, user_id=user_id).first()

    if selected_app:
        # Reset all others to False
        UniversityApplication.query.filter_by(user_id=user_id).update({'is_final_choice': False})
        selected_app.is_final_choice = True
        db.session.commit()
        flash(f"{selected_app.university_name} marked as your final choice.", "success")
    else:
        flash("Application not found or unauthorized.", "danger")

    return redirect(url_for('university_tracker'))

# Route: Dashboard (protected)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please login to continue.", "warning")
        return redirect(url_for('login'))

    return render_template('dashboard.html', name=session.get('user_name'))

# Route: I-20 & SEVIS Fee Step
@app.route('/i20-process', methods=['GET', 'POST'])
def i20_process():
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        flash("I-20 & SEVIS step marked as complete.", "success")
        return redirect(url_for('visa_process'))  # next step placeholder

    return render_template('i20_process.html')


@app.route('/visa-process', methods=['GET', 'POST'])
def visa_process():
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        flash("Visa process step marked as complete.", "success")
        # Inside visa_process() route:
        return redirect(url_for('travel_ready'))  # ✅ Corrected
    # next step placeholder

    return render_template('visa_process.html')


@app.route('/travel-ready', methods=['GET', 'POST'])
def travel_ready():
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        flash("You're all packed and ready to go! ✈️", "success")
        return redirect(url_for('post_arrival_guide'))  # next step placeholder

    return render_template('travel_ready.html')

@app.route('/post-arrival-guide', methods=['GET', 'POST'])
def post_arrival_guide():
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        flash("Post-arrival step marked complete! 🎓", "success")
        return redirect(url_for('subjects'))  # ✅ Redirect to subjects

    return render_template('post_arrival_guide.html')

@app.route('/subjects', methods=['GET', 'POST'])
def subjects():
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        semester = request.form['semester']
        subject = request.form['subject']
        grade = request.form['grade']

        new_entry = SubjectGrade(
            user_id=user_id,
            semester=semester,
            subject=subject,
            grade=grade
        )
        db.session.add(new_entry)
        db.session.commit()
        flash("Subject & grade added!", "success")
        return redirect(url_for('subjects'))

    grades = SubjectGrade.query.filter_by(user_id=user_id).all()
    return render_template('subjects.html', grades=grades)

from datetime import datetime, timedelta  # ✅ Required for date calculations

from datetime import datetime, timedelta  # ✅ Make sure this is at the top of your file

@app.route('/opt-guide', methods=['GET', 'POST'])
def opt_guide():
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))

    if request.method == 'POST':
        grad_date_str = request.form.get('graduation_date')
        preferred_start_str = request.form.get('preferred_start_date')

        if not grad_date_str or not preferred_start_str:
            flash("Both dates are required.", "danger")
            return redirect(url_for('opt_guide'))

        try:
            grad_date = datetime.strptime(grad_date_str, '%Y-%m-%d')
            preferred_start = datetime.strptime(preferred_start_str, '%Y-%m-%d')

            earliest = grad_date - timedelta(days=90)
            latest = grad_date + timedelta(days=60)

            if earliest <= preferred_start <= latest:
                flash("✅ OPT dates valid! You're ready to prepare your application.", "success")
                return redirect(url_for('skills_page'))  # Update this to your next page
            else:
                flash("⚠️ Start date is not within the valid OPT window (90 days before to 60 days after graduation).", "danger")
        except ValueError:
            flash("❌ Invalid date format. Please use YYYY-MM-DD.", "danger")

    return render_template('opt_guide.html')


@app.route('/skills')
def skills_page():
    if 'user_id' not in session:
        flash("Please login first.", "warning")
        return redirect(url_for('login'))

    return render_template('skills.html')




# Route: Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


# Initialize DB (run only once)
if __name__ == '__main__':
    if not os.path.exists('users.db'):
        with app.app_context():
            db.create_all()
    app.run(debug=True)
