import ssl
import secrets
from datetime import datetime
from paho import mqtt
from flask import Flask, render_template, request, session, redirect, url_for, json, flash
from flask_mqtt import Mqtt
from service.user_service import (validate_registration, add_user, authenticate_user, get_current_user, delete_employee,
                                  get_stock, update_database, get_departments, get_employees, update_department,
                                  update_card_access, get_cards, card_exists, store_card, store_access_log,
                                  retrieve_data, delete_access_log, get_access_log)

app = Flask(__name__)
app.secret_key = secrets.token_hex()

app.config['MQTT_BROKER_URL'] = "a2521ac553aa46f7909aaa37b9b21dbc.s1.eu.hivemq.cloud"
app.config['MQTT_USERNAME'] = "Group_work"
app.config['MQTT_PASSWORD'] = "RFIDproject1"
app.config['MQTT_CLIENT_ID'] = "Adrianna2.0"
app.config['MQTT_BROKER_PORT'] = 8883
app.config['MQTT_KEEPALIVE'] = 60
app.config['MQTT_TLS_ENABLED'] = True
app.config['MQTT_TLS_INSECURE'] = False
app.config['MQTT_TLS_CA_CERTS'] = 'isrgrootx1.pem'
app.config['MQTT_TLS_VERSION'] = ssl.PROTOCOL_TLSv1_2
app.config['MQTT_TLS_CIPHERS'] = None


mqtt = Mqtt(app)

subscribe_topic = "RFID/security"
publish_topic = "RFID/name"

gate_data = []


@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    if rc == 0:
        mqtt.subscribe(subscribe_topic)
    else:
        print('Bad connection. Code:', rc)


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    global gate_data
    with app.app_context():
        try:
            data = json.loads(message.payload.decode())
            if message.topic == subscribe_topic and 'uid' in data:
                uid = data['uid']
                if not card_exists(uid):
                    store_card(uid)
                    gate_data.append(data)
                    print('Received message on topic: {topic} with payload: {payload}'.format(topic=message.topic,
                                                                                              payload=data))
                else:
                    print('UID exists in the database:', uid)
                card_number = uid
                access = data.get('Access', 'Unknown')
                access_datetime = datetime.now()
                store_access_log(card_number, access, access_datetime)
                employee_data = retrieve_data(card_number)

                if employee_data:
                    publish_data(employee_data)
                else:
                    print("No employee found for card number:", card_number)
            else:
                print('Received invalid MQTT message:', data)
        except Exception as e:
            print('Error handling MQTT message:', e)


def publish_data(employee_data):
    try:
        if 'card_number' in employee_data and 'FirstName' in employee_data:
            uid = employee_data['card_number']
            name = employee_data['FirstName']
            data = {
                "name": name,
                "uid": uid
            }
            mqtt.publish(publish_topic, json.dumps(data))
            print("Published data to topic:", publish_topic)
        else:
            print("Error publishing employee data: Incomplete employee data")
    except Exception as e:
        print("Error publishing employee data:", e)


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/publish', methods=['POST'])
def publish_message():
    request_data = request.get_json()
    publish_result = mqtt.publish(request_data['topic'], request_data['msg'])
    return {'code': publish_result[0]}


@app.route('/')
def index():
    if 'email' not in session:
        return redirect(url_for('home'))
    email = get_current_user()
    stock_updated = request.args.get('stock_updated', default=False, type=bool)
    return render_template('index.html', user=email, stock_updated=stock_updated)


@app.route('/register', methods=['GET', 'POST'])
def register():
    user = get_current_user()
    if request.method == 'GET':
        return render_template('register.html', user=user)
    errors = validate_registration(request.form)
    if any(len(errors[key]) > 0 for key in errors.keys()):
        return render_template('register.html', has_errors=True, errors=errors, form_values=request.form)
    added_user = add_user(request.form)
    return render_template('index.html', user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'email' in session:
        return redirect(url_for('index'))
    if request.method == 'GET':
        return render_template('login.html')
    if 'default_password' in request.form:
        flash('Please change your default password.', 'info')
        return render_template('create_password.html')
    is_authenticated = authenticate_user(request.form)
    if not is_authenticated:
        flash('Invalid email or password. Please try again.', 'error')
        return render_template('login.html', has_errors=True)
    session['email'] = request.form['email']
    flash('Login successful!', 'success')
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('home'))


@app.route('/stock', methods=['GET'])
def view_stock():
    if 'email' not in session:
        return redirect(url_for('home'))
    stock_details = get_stock()
    return render_template('stock.html', user=session['email'], stock_details=stock_details)


@app.route('/update_stock', methods=['POST'])
def update_stock():
    ingredient_id = request.form.get('ingredient_id')
    action = request.form.get('action')
    quantity = int(request.form.get('quantity'))
    update_database(ingredient_id, action, quantity)
    return redirect(url_for('index', stock_updated=True))


@app.route('/employees', methods=['GET'])
def view_employees():
    if 'email' not in session:
        return redirect(url_for('home'))
    employees_details = get_employees()
    departments = get_departments()
    cards = get_cards()
    return render_template('employees.html', user=session['email'], employees_details=employees_details,
                           departments=departments, cards=cards)


@app.route('/delete_employee', methods=['POST'])
def remove_employee():
    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        if employee_id:
            success = delete_employee(employee_id)
            if success:
                flash('Employee deleted successfully', 'success')
            else:
                flash('Failed to delete employee', 'error')
            return redirect(url_for('view_employees'))


@app.route('/update_dep', methods=['POST'])
def update_department_route():
    employee_id = request.form.get('employee_id')
    new_department = request.form.get('new_department')
    update_department(employee_id, new_department)
    return redirect(url_for('index', department_updated=True))


@app.route('/update_card', methods=['POST'])
def update_card_route():
    employee_id = request.form.get('employee_id')
    new_card = request.form.get('new_card')
    if update_card_access(employee_id, new_card):
        return redirect(url_for('index', card_updated=True))
    else:
        flash('Failed to update the card.', 'error')
        return redirect(url_for('index'))


@app.route('/access_log', methods=['GET'])
def load_access_table():
    if 'email' not in session:
        return redirect(url_for('home'))
    access_log = get_access_log()
    return render_template('accesslog.html', user=session['email'], access_log=access_log,
                           access_log_updated=True)


@app.route('/delete_log', methods=['POST'])
def delete_log():
    if request.method == 'POST':
        log_id = request.form.get('log_id')
        if log_id:
            success = delete_access_log(log_id)  # Implement this function to delete the access log entry
            if success:
                flash('Access log entry deleted successfully', 'success')
            else:
                flash('Failed to delete access log entry', 'error')
            return redirect(url_for('load_access_table'))


if __name__ == '__main__':
    app.run(debug=True)
