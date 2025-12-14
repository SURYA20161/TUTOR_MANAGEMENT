from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
import os

app = Flask(__name__)
app.secret_key = "tutor_secret"
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# ---------------- MongoDB Connection ----------------
client = MongoClient("mongodb://localhost:27017/")
db = client['tutor_db']
tutors_col = db['tutors']
students_col = db['students']

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


# ---------------- Home ----------------
@app.route('/')
def home():
    return redirect(url_for('login'))


# ---------------- Register ----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        photo = request.files.get('photo')

        if tutors_col.find_one({'username': username}):
            flash("Username already exists!", "danger")
            return redirect(url_for('register'))

        filename = None
        if photo and photo.filename:
            filename = photo.filename
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        tutors_col.insert_one({
            'username': username,
            'email': email,
            'password': password,
            'photo': filename
        })

        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')


# ---------------- Login ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        tutor = tutors_col.find_one({'username': username, 'password': password})
        if tutor:
            session['user'] = username
            flash("Login successful!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password!", "danger")

    return render_template('login.html')


# ---------------- Dashboard ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = session['user']
    tutor = tutors_col.find_one({'username': user})
    user_students = list(students_col.find({'tutor': user}))
    return render_template('dashboard.html', students=user_students, tutor=tutor)


# ---------------- Add Student ----------------
@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = session['user']

    if request.method == 'POST':
        name = request.form['name']
        rollno = request.form['rollno']
        year = request.form['year']
        cgpa = request.form['cgpa']
        details = request.form['details']
        photo = request.files.get('photo')

        filename = None
        if photo and photo.filename:
            filename = photo.filename
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        students_col.insert_one({
            'tutor': user,
            'name': name,
            'rollno': rollno,
            'year': year,
            'cgpa': cgpa,
            'details': details,
            'photo': filename
        })

        flash("Student added successfully!", "success")
        return redirect(url_for('dashboard'))

    tutor = tutors_col.find_one({'username': user})
    return render_template('add_student.html', tutor=tutor)


# ---------------- Update Student ----------------
@app.route('/update_student/<student_id>', methods=['GET', 'POST'])
def update_student(student_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    student = students_col.find_one({'_id': ObjectId(student_id)})
    if not student:
        flash("Student not found!", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        rollno = request.form['rollno']
        year = request.form['year']
        cgpa = request.form['cgpa']
        details = request.form['details']
        photo = request.files.get('photo')

        update_data = {
            'name': name,
            'rollno': rollno,
            'year': year,
            'cgpa': cgpa,
            'details': details
        }

        if photo and photo.filename:
            filename = photo.filename
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            update_data['photo'] = filename

        students_col.update_one({'_id': ObjectId(student_id)}, {'$set': update_data})
        flash("Student details updated!", "info")
        return redirect(url_for('dashboard'))

    return render_template('update_student.html', student=student)


# ---------------- Delete Student ----------------
@app.route('/delete_student/<student_id>')
def delete_student(student_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    students_col.delete_one({'_id': ObjectId(student_id)})
    flash("Student deleted successfully!", "danger")
    return redirect(url_for('dashboard'))


# ---------------- Tutor Profile ----------------
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = session['user']
    tutor = tutors_col.find_one({'username': user})

    if request.method == 'POST':
        new_username = request.form['username']
        new_email = request.form['email']
        password = request.form['password']
        photo = request.files.get('photo')

        if new_username != user and tutors_col.find_one({'username': new_username}):
            flash("Username already exists!", "danger")
            return redirect(url_for('profile'))

        update_data = {'username': new_username, 'email': new_email}
        if password:
            update_data['password'] = password
        if photo and photo.filename:
            filename = photo.filename
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            update_data['photo'] = filename

        tutors_col.update_one({'username': user}, {'$set': update_data})

        # Update username in session & related students
        if new_username != user:
            students_col.update_many({'tutor': user}, {'$set': {'tutor': new_username}})
            session['user'] = new_username

        flash("Profile updated successfully!", "success")
        return redirect(url_for('dashboard'))

    return render_template('profile.html', tutor=tutor)


# ---------------- Logout ----------------
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash("Logged out successfully.", "secondary")
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
