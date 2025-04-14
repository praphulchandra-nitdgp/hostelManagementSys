from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector
from config import DB_CONFIG
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey'

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

@app.route('/manager', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return "Username or password missing"

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admin WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['admin'] = True
            return redirect('/dashboard')
        else:
            return "Invalid credentials"

    return render_template('login.html')

@app.route('/', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        name = request.form['name']
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students WHERE name=%s", (name,))
        student = cursor.fetchone()
        conn.close()
        if student:
            session['student_id'] = student['id']
            return redirect('/student_dashboard')
        else:
            return "Student not found"
    return render_template('student/student_login.html')

@app.route('/student_register', methods=['GET', 'POST'])
def student_register():
    if request.method == 'POST':
        college_id = request.form['student_id']
        name = request.form['name']
        password = generate_password_hash(request.form['password'])
        amount = request.form['amount']

        if not amount:
            return "Amount is required for registration."

        # Ensure that the amount is converted to a decimal type
        try:
            amount = float(amount)
        except ValueError:
            return "Invalid amount format."

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO students (college_id, name, password, payment_status, amount_payable) VALUES (%s, %s, %s, 'Pending', %s)",
            (college_id, name, password, amount)
        )
        conn.commit()
        conn.close()

        return redirect('/')

    # GET request logic
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM rooms WHERE is_occupied = 0")
    rooms = cursor.fetchall()
    conn.close()
    
    return render_template('student/student_register.html', rooms=rooms)


@app.route('/student_dashboard')
def student_dashboard():
    if 'student_id' not in session:
        return redirect('/')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students WHERE id = %s", (session['student_id'],))
    student = cursor.fetchone()
    conn.close()
    return render_template('student/student_dashboard.html', student=student)

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    if 'student_id' not in session:
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        student_id = request.form['student_id']
        amount = request.form['amount']
        # Update the student's payment status and amount payable
        cursor.execute("""
            UPDATE students 
            SET payment_status = 'Paid', amount_payable = %s 
            WHERE id = %s
        """, (amount, student_id))
        conn.commit()
        conn.close()
        return redirect('/student_dashboard')

    cursor.execute("SELECT * FROM students WHERE id = %s", (session['student_id'],))
    student = cursor.fetchone()
    conn.close()

    return render_template('student/payment.html', student=student)

@app.route('/dashboard')
def dashboard():
    if not session.get('admin'):
        return redirect('/manager')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS total_students FROM students")
    total_students = cursor.fetchone()['total_students']

    cursor.execute("SELECT COUNT(*) AS occupied_rooms FROM rooms WHERE is_occupied = 1")
    occupied_rooms = cursor.fetchone()['occupied_rooms']

    cursor.execute("SELECT COUNT(*) AS pending_payments FROM students WHERE payment_status = 'Pending'")
    pending_payments = cursor.fetchone()['pending_payments']

    conn.close()
    return render_template('dashboard.html', stats={
        'total_students': total_students,
        'occupied_rooms': occupied_rooms,
        'pending_payments': pending_payments
    })

@app.route('/students')
def students():
    if not session.get('admin'):
        return redirect('/manager')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    conn.close()
    return render_template('students.html', students=students)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if not session.get('admin'):
        return redirect('/manager')
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        room_id = request.form['room_id']
        payment_status = request.form['payment_status']
        check_in = datetime.now()
        amount = request.form['amount']

        cursor.execute("SELECT is_occupied FROM rooms WHERE id = %s", (room_id,))
        if cursor.fetchone()[0]:
            return "Room is already occupied"

        cursor.execute("INSERT INTO students (name, room_id, payment_status, check_in, amount_payable) VALUES (%s, %s, %s, %s, %s)",
                       (name, room_id, payment_status, check_in, amount))
        cursor.execute("UPDATE rooms SET is_occupied = 1 WHERE id = %s", (room_id,))
        conn.commit()
        conn.close()
        return redirect('/students')
    else:
        cursor.execute("SELECT * FROM rooms WHERE is_occupied = 0")
        rooms = cursor.fetchall()
        conn.close()
        return render_template('add_student.html', rooms=rooms)

@app.route('/checkout/<int:student_id>')
def checkout(student_id):
    if not session.get('admin'):
        return redirect('/manager')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT room_id FROM students WHERE id = %s", (student_id,))
    room_id = cursor.fetchone()[0]
    cursor.execute("UPDATE rooms SET is_occupied = 0 WHERE id = %s", (room_id,))
    cursor.execute("UPDATE students SET check_out = %s WHERE id = %s", (datetime.now(), student_id))
    conn.commit()
    conn.close()
    return redirect('/students')

@app.route('/payments', methods=['GET', 'POST'])
def payments():
    if not session.get('admin'):
        return redirect('/manager')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if request.method == 'POST':
        student_id = request.form['student_id']
        cursor.execute("UPDATE students SET payment_status = 'Paid' WHERE id = %s", (student_id,))
        conn.commit()
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    conn.close()
    return render_template('payments.html', students=students)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
