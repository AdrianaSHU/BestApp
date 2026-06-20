from flask import session
import bcrypt
from db import get_db


def validate_field_not_empty(field, field_name):
    errors = []
    if len(field) == 0:
        errors.append(f'{field_name} cannot be empty')
    return errors


def validate_username(email):
    empty_email = validate_field_not_empty(email, 'Email')
    if len(empty_email) > 0:
        return empty_email
    if len(email) < 3:
        return ['Email must be at least 3 characters long']
    db = get_db()
    cur = db.execute("SELECT * FROM Users WHERE Email=?", [email])
    results = cur.fetchall()
    if len(results) > 0:
        return ['User with this email already exists']
    return []


def validate_passwords(password, confirm_password):
    errors = []
    if len(password) < 8:
        errors.append('Password must be at least 8 characters long.')
    if not any(char.isupper() for char in password) or \
            not any(char.isdigit() for char in password) or \
            not any(char.islower() for char in password):
        errors.append('Password must contain at least one uppercase character, one lowercase character and one digit.')
    if password != confirm_password:
        errors.append('Passwords must match')
    return errors


def validate_registration(user_form_values):
    name = user_form_values.get('name')
    surname = user_form_values.get('surname')
    password = user_form_values.get('password')
    confirm_password = user_form_values.get('confirm_password')

    errors = {
        'name': validate_field_not_empty(name, "First name"),
        'surname': validate_field_not_empty(surname, 'Surname'),
        'password': validate_passwords(password, confirm_password)
    }
    return errors


def add_user(user_form_values):
    first_name = user_form_values['name']
    last_name = user_form_values['surname']
    email = user_form_values['email']
    password = user_form_values['password']
    department_id = user_form_values['department_id']
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)

    db = get_db()
    db.execute('INSERT INTO Employees (FirstName, LastName, DepartmentID) VALUES (?, ?, ?)',
               (first_name, last_name, department_id))
    db.commit()
    cur = db.execute('SELECT EmployeeID FROM Employees WHERE FirstName = ? AND LastName = ? AND DepartmentID = ?',
                     (first_name, last_name, department_id))
    employee_id = cur.fetchone()[0]
    db.execute('INSERT INTO Users (Email, Password) VALUES (?, ?)',
               (email, hashed_password.decode()))
    db.commit()
    cur = db.execute('SELECT UserID FROM Users WHERE Email = ?', (email,))
    user_id = cur.fetchone()[0]
    db.execute('UPDATE Employees SET UserID = ? WHERE EmployeeID = ?', (user_id, employee_id))
    db.commit()


def authenticate_user(user_values, default_password=None):
    email = user_values['email']
    password = user_values['password']
    db = get_db()
    cur = db.execute('SELECT * FROM Users WHERE Email = ?', [email])
    user_row = cur.fetchone()
    if user_row:
        hashed_password = user_row['Password']
        if bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')):
            if default_password and hashed_password == bcrypt.hashpw(default_password.encode('utf-8'), hashed_password.encode('utf-8')).decode('utf-8'):
                return 'default_password'
            else:
                return 'valid_user'
        else:
            return 'incorrect_password'
    else:
        return 'user_not_found'


def get_current_user():
    if 'email' in session:
        email = session['email']
        db = get_db()
        cur = db.execute('SELECT * FROM Users WHERE Email = ?', [email])
        user_row = cur.fetchone()
        if user_row:
            user_id = user_row[0]
            cur = db.execute('SELECT * FROM Employees WHERE UserID = ?', [user_id])
            employee_row = cur.fetchone()
            if employee_row:
                first_name = employee_row[1]
                last_name = employee_row[2]
                department_id = employee_row[3]
                cur = db.execute('SELECT DepartmentName FROM Departments WHERE DepartmentID = ?', [department_id])
                department_row = cur.fetchone()
                if department_row:
                    department_name = department_row[0]
                else:
                    department_name = None

                user_details = {
                    'UserID': user_id,
                    'Email': email,
                    'FirstName': first_name,
                    'LastName': last_name,
                    'DepartmentName': department_name,
                    'DepartmentID': department_id
                }
                return user_details
    return None


def get_stock():
    db = get_db()
    cur = db.execute('SELECT * FROM Stock')
    stock_details = cur.fetchall()
    return stock_details


def update_database(ingredient_id, action, quantity):
    db = get_db()
    if action == 'add':
        db.execute("UPDATE Stock SET Quantity = Quantity + ? WHERE IngredientID = ?", [quantity, ingredient_id])
    elif action == 'subtract':
        db.execute("UPDATE Stock SET Quantity = CASE WHEN Quantity - ? < 0 THEN 0 ELSE Quantity - ? END"
                   " WHERE IngredientID = ?", [quantity, quantity, ingredient_id])
    db.commit()


def get_employees():
    db = get_db()
    cur = db.execute("""
        SELECT Employees.EmployeeID, Employees.FirstName || ' ' || Employees.LastName AS FullName, 
               Departments.DepartmentName, Users.Email, Access_cards.card_number
        FROM Employees
        INNER JOIN Departments ON Employees.DepartmentID = Departments.DepartmentID
        INNER JOIN Users ON Employees.UserID = Users.UserID
        LEFT JOIN Access_cards ON Employees.EmployeeID = Access_cards.EmployeeID
    """)
    employees_details = cur.fetchall()
    return employees_details


def get_departments():
    db = get_db()
    cur = db.execute("SELECT DepartmentName FROM Departments")
    departments = [row[0] for row in cur.fetchall()]
    return departments


def update_department(employee_id, new_department):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT DepartmentID FROM Departments WHERE DepartmentName = ?", (new_department,))
    department_id = cur.fetchone()

    if department_id:
        department_id = department_id[0]
        cur.execute("UPDATE Employees SET DepartmentID = ? WHERE EmployeeID = ?", (department_id, employee_id))
        db.commit()
        return True
    else:
        return False


def get_cards():
    db = get_db()
    cur = db.execute("SELECT card_number FROM Access_cards WHERE EmployeeID IS NULL")
    cards = [row[0] for row in cur.fetchall()]
    return cards


def card_exists(uid):
    db = get_db()
    cur = db.execute("SELECT card_number FROM Access_cards WHERE card_number = ?", (uid,))
    result = cur.fetchone()
    return result is not None


def store_card(uid):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT card_number FROM Access_cards WHERE card_number = ?", (uid,))
    result = cur.fetchone()
    if result is None:
        cur.execute("INSERT INTO Access_cards (card_number) VALUES (?)", (uid,))
        db.commit()


def update_card_access(employee_id, new_card):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT EmployeeID FROM Employees WHERE EmployeeID = ?", (employee_id,))
    employee_exists = cur.fetchone()

    if employee_exists:
        cur.execute("UPDATE Access_cards SET EmployeeID = ? WHERE card_number = ? AND EmployeeID IS NULL",
                    (employee_id, new_card))
        db.commit()
        return True
    else:
        return False


def store_access_log(card_number, access, access_datetime):
    db = get_db()
    cur = db.execute("SELECT EmployeeID FROM Access_cards WHERE card_number = ? AND EmployeeID IS NOT NULL",
                     (card_number,))
    assigned_employee = cur.fetchone()
    if assigned_employee:
        access = "Granted"
    else:
        access = "Denied"
    db.execute("INSERT INTO Access_Log (card_number, Access, AccessDateTime) VALUES (?, ?, ?)",
               (card_number, access, access_datetime))
    db.commit()


def delete_employee(employee_id):
    db = get_db()
    try:
        db.execute("DELETE FROM Employees WHERE EmployeeID = ?", [employee_id])
        db.commit()
        return True
    except Exception as e:
        print(f"Error deleting employee: {e}")
        db.rollback()
        return False


def retrieve_data(card_number):
    try:
        db = get_db()
        cur = db.execute("SELECT Access_cards.card_number, Employees.FirstName \
                          FROM Access_cards \
                          LEFT JOIN Employees ON Access_cards.EmployeeID = Employees.EmployeeID \
                          WHERE Access_cards.card_number = ?", (card_number,))
        employee_data = cur.fetchone()
        if employee_data:
            return {'card_number': employee_data[0], 'FirstName': employee_data[1]}
        else:
            return None
    except Exception as e:
        print("Error retrieving employee data:", e)
        return None


def get_access_log():
    db = get_db()
    cur = db.execute("SELECT * FROM Access_Log")
    access_log = cur.fetchall()
    return access_log


def delete_access_log(log_id):
    try:
        db = get_db()
        db.execute("DELETE FROM Access_Log WHERE LogID = ?", [log_id])
        db.commit()
        return True
    except Exception as e:
        print(f"Error deleting access log entry: {e}")
        db.rollback()
        return False
