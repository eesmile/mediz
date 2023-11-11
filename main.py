from flask import Flask, render_template, request, redirect, url_for, session
import pymysql
from config import host, port, user, password, db_name

from datetime import datetime

app = Flask(__name__)
app.secret_key = 'JDS3r23234DSBFjklnsdkjfbsdlhfsd'
db = pymysql.connect(host=host, port=port, user=user, password=password, database=db_name)
cursor = db.cursor()


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        age = request.form['age']

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            return render_template('register.html', error='Пользователь с таким именем уже существует')

        cursor.execute("""
        INSERT INTO users (username, password, first_name, last_name, age)
        VALUES (%s, %s, %s, %s, %s)
        """, (username, password, first_name, last_name, age))
        db.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()

        if user:
            session['user'] = {
                'id': user[0],
                'username': user[1],
                'first_name': user[3],
                'last_name': user[4],
                'age': user[5]
            }
            return redirect(url_for('profile'))
        else:
            return render_template('login.html', error='Неверное имя пользователя или пароль')

    return render_template('login.html')


@app.route('/profile')
def profile():
    if 'user' in session:
        user = session['user']
        return render_template('profile.html', user=user)
    else:
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))


@app.route('/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    if 'user' in session:
        user = session['user']

        if request.method == 'POST':
            doctor_name = request.form['doctor_name']
            specialization = request.form['specialization']
            photo = request.files['photo']

            cursor.execute("""
            INSERT INTO doctors (name, specialization, photo)
            VALUES (%s, %s, %s)
            """, (doctor_name, specialization, photo.filename))
            db.commit()

            photo.save(f'uploads/{photo.filename}')

            success_message = "Новый врач успешно добавлен!"
            return render_template('add_doctor.html', user=user, success_message=success_message)

        return render_template('add_doctor.html', user=user)
    else:
        return redirect(url_for('login'))


@app.route('/add_medicine', methods=['GET', 'POST'])
def add_medicine():
    if 'user' in session:
        user = session['user']

        if request.method == 'POST':
            medicine_name = request.form['medicine_name']
            price = request.form['price']
            photo = request.files['photo']

            cursor.execute("""
            INSERT INTO medicines (name, price, photo)
            VALUES (%s, %s, %s)
            """, (medicine_name, price, photo.filename))
            db.commit()

            photo.save(f'uploads/{photo.filename}')

            success_message = "Новая таблетка успешно добавлена!"
            return render_template('add_medicine.html', user=user, success_message=success_message)

        return render_template('add_medicine.html', user=user)
    else:
        return redirect(url_for('login'))


@app.route('/appoint_doctor', methods=['GET', 'POST'])
def appoint_doctor():
    if 'user' in session:
        user = session['user']

        # Получение списка существующих врачей из базы данных
        cursor.execute("SELECT * FROM doctors")
        doctors = cursor.fetchall()

        if request.method == 'POST':
            doctor_id = request.form['doctor_id']
            appointment_time = request.form['appointment_time']

            # Добавление записи к врачу в базу данных
            cursor.execute("""
            INSERT INTO appointments (user_id, doctor_id, appointment_time)
            VALUES (%s, %s, %s)
            """, (user['id'], doctor_id, appointment_time))
            db.commit()

            success_message = "Запись к врачу успешно добавлена!"
            return render_template('appoint_doctor.html', user=user, doctors=doctors, success_message=success_message)

        return render_template('appoint_doctor.html', user=user, doctors=doctors)
    else:
        return redirect(url_for('login'))


@app.route('/user_appointments', methods=['GET', 'POST'])
def user_appointments():
    if 'user' in session:
        user = session['user']

        cursor.execute("""
        SELECT appointments.id, doctors.name, doctors.specialization, 
        DATE_FORMAT(appointments.appointment_time, '%%d.%%m.%%Y %%H:%%i'), 
        appointments.appointment_time > NOW()
        FROM appointments
        JOIN doctors ON appointments.doctor_id = doctors.id
        WHERE appointments.user_id = %s
        ORDER BY appointments.appointment_time DESC
        """, (user['id'],))
        user_appointments = cursor.fetchall()

        if request.method == 'POST':
            search_name = request.form.get('search_name', '')
            search_date = request.form.get('search_date', '')

            query = """
            SELECT appointments.id, doctors.name, doctors.specialization, 
            DATE_FORMAT(appointments.appointment_time, '%%d.%%m.%%Y %%H:%%i'), 
            appointments.appointment_time > NOW()
            FROM appointments
            JOIN doctors ON appointments.doctor_id = doctors.id
            WHERE appointments.user_id = %s
            """
            params = (user['id'],)

            if search_name:
                query += " AND doctors.name LIKE %s"
                params += (f'%{search_name}%',)
            if search_date:
                query += " AND DATE_FORMAT(appointments.appointment_time, '%%Y-%%m-%%d') = %s"
                params += (search_date,)

            query += " ORDER BY appointments.appointment_time DESC"

            cursor.execute(query, params)
            user_appointments = cursor.fetchall()

        return render_template('user_appointments.html', user=user, user_appointments=user_appointments)
    else:
        return redirect(url_for('login'))


@app.route('/delete_appointment/<int:appointment_id>', methods=['POST'])
def delete_appointment(appointment_id):
    if 'user' in session:
        user = session['user']

        cursor.execute("SELECT * FROM appointments WHERE id = %s", (appointment_id,))
        appointment = cursor.fetchone()

        if appointment and appointment[1] == user['id']:
            cursor.execute("DELETE FROM appointments WHERE id = %s", (appointment_id,))
            db.commit()

        return redirect(url_for('user_appointments'))
    else:
        return redirect(url_for('login'))


@app.route('/products', methods=['GET'])
def products():
    # Получение списка товаров из базы данных
    cursor.execute("SELECT * FROM medicines")
    medicines = cursor.fetchall()

    return render_template('products.html', medicines=medicines)


@app.route('/cart', methods=['GET'])
def cart():
    if 'user' in session:
        user = session['user']

        cursor.execute("""
        SELECT medicines.id, medicines.name, medicines.price, cart.quantity
        FROM medicines
        JOIN cart ON medicines.id = cart.medicine_id
        WHERE cart.user_id = %s
        """, (user['id'],))
        cart_items = cursor.fetchall()

        return render_template('cart.html', user=user, cart_items=cart_items)
    else:
        return redirect(url_for('login'))


@app.route('/add_to_cart/<int:medicine_id>', methods=['POST'])
def add_to_cart(medicine_id):
    if 'user' in session:
        user = session['user']

        cursor.execute("SELECT * FROM cart WHERE user_id = %s AND medicine_id = %s", (user['id'], medicine_id))
        existing_item = cursor.fetchone()

        if existing_item:

            cursor.execute("UPDATE cart SET quantity = quantity + 1 WHERE id = %s", (existing_item[0],))
        else:

            cursor.execute("INSERT INTO cart (user_id, medicine_id, quantity) VALUES (%s, %s, 1)", (user['id'], medicine_id))

        db.commit()

        return redirect(url_for('cart'))
    else:
        return redirect(url_for('login'))


@app.route('/remove_from_cart/<int:medicine_id>', methods=['POST'])
def remove_from_cart(medicine_id):
    if 'user' in session:
        user = session['user']

        cursor.execute("DELETE FROM cart WHERE user_id = %s AND medicine_id = %s", (user['id'], medicine_id))
        db.commit()

        return redirect(url_for('cart'))
    else:
        return redirect(url_for('login'))


@app.route('/place_order', methods=['POST'])
def place_order():
    if 'user' in session:
        user = session['user']

        cursor.execute("INSERT INTO orders (user_id) VALUES (%s)", (user['id'],))
        db.commit()

        cursor.execute("SELECT LAST_INSERT_ID()")
        order_id = cursor.fetchone()[0]

        cursor.execute("SELECT * FROM cart WHERE user_id = %s", (user['id'],))
        cart_items = cursor.fetchall()

        for item in cart_items:
            cursor.execute("INSERT INTO order_items (order_id, medicine_id, quantity) VALUES (%s, %s, %s)",
                           (order_id, item[2], item[3]))

        cursor.execute("DELETE FROM cart WHERE user_id = %s", (user['id'],))
        db.commit()

        success_message = "Заказ успешно оформлен!"

        return render_template('order_placed.html', user=user, success_message=success_message)
    else:
        return redirect(url_for('login'))


@app.route('/user_orders')
def user_orders():
    if 'user' in session:
        user = session['user']

        cursor.execute("""
        SELECT orders.id, orders.order_time, GROUP_CONCAT(medicines.name, ' x ', order_items.quantity) AS items
        FROM orders
        JOIN order_items ON orders.id = order_items.order_id
        JOIN medicines ON order_items.medicine_id = medicines.id
        WHERE orders.user_id = %s
        GROUP BY orders.id
        ORDER BY orders.order_time DESC
        """, (user['id'],))
        user_orders = cursor.fetchall()

        return render_template('user_orders.html', user=user, user_orders=user_orders)
    else:
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
