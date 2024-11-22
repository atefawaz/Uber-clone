import functools
from flask import Flask, render_template, request, redirect, session, url_for, flash,g,jsonify
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
import socketio
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
import sqlite3
from pymongo import MongoClient
from flask_cors import CORS
from bson import ObjectId
from flask_socketio import SocketIO,emit,join_room

# Connect to MongoDB
client = MongoClient('mongodb:/(your url mongo compas )')
db = client['uber_clone']  
collection = db['user_orders']  
collection_drivers_data = db['drivers_data']
collection_orders_backup = db['orders_backup']


app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)
app.config['SECRET_KEY'] = 'secret_key'



bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


conn_users = sqlite3.connect('users.db')
cursor_users = conn_users.cursor()

conn_drivers = sqlite3.connect('drivers.db')

cursor_drivers = conn_drivers.cursor()

cursor_users.execute('''
   CREATE TABLE IF NOT EXISTS users (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       name TEXT NOT NULL,
       lastname TEXT NOT NULL,
       birthdate DATE NOT NULL,
       username TEXT NOT NULL,
       password TEXT NOT NULL
   )
''')
conn_users.commit()


cursor_drivers.execute('''
   CREATE TABLE IF NOT EXISTS drivers (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       name TEXT NOT NULL,
       lastname TEXT NOT NULL,
       username TEXT NOT NULL,
       password TEXT NOT NULL
       
   )
''')
conn_drivers.commit()





# Function to get the database connection
def get_db_users():
    db_users = getattr(g, '_database_users', None)
    if db_users is None:
        db_users = g._database_users = sqlite3.connect('users.db')
    return db_users

def get_db_drivers():
    db_drivers = getattr(g, '_database_drivers', None)
    if db_drivers is None:
        db_drivers = g._database_drivers = sqlite3.connect('drivers.db')
    return db_drivers

# Teardown function to close the database connection
@app.teardown_appcontext
def close_connection(exception):
    db_users = getattr(g, '_database_users', None)
    if db_users is not None:
        db_users.close()
    
    db_drivers = getattr(g, '_database_drivers', None)
    if db_drivers is not None:
        db_drivers.close()


class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username




@login_manager.user_loader
def load_user(user_id):
    # Check the users table for the user ID
    conn_users = get_db_users()
    cursor_users = conn_users.cursor()
    cursor_users.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user_data = cursor_users.fetchone()

    if user_data:
        user = User(user_data[0], user_data[4])  # Create a User object
        return user

    # Check the drivers table for the driver ID if not found in the users table
    conn_drivers = get_db_drivers()
    cursor_drivers = conn_drivers.cursor()
    cursor_drivers.execute('SELECT * FROM drivers WHERE id = ?', (user_id,))
    driver_data = cursor_drivers.fetchone()

    if driver_data:
        driver = User(driver_data[0], driver_data[3])  # Create a User object for driver
        return driver

    return None  # Return None if no user or driver found with the provided ID


class UserRegistrationForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired(), Length(min=2, max=50)])
    lastname = StringField('Last Name', validators=[InputRequired(), Length(min=2, max=50)])
    birthdate = StringField('Birth Date', validators=[InputRequired()])
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=80)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=120)])
    submit = SubmitField('Sign Up')



class DriverRegistrationForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired(), Length(min=2, max=50)])
    lastname = StringField('Last Name', validators=[InputRequired(), Length(min=2, max=50)])
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=80)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=120)])
    submit = SubmitField('Sign Up')





class DriverInfoForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired(), Length(min=2, max=50)])
    lastname = StringField('Last Name', validators=[InputRequired(), Length(min=2, max=50)])
    birthdate = StringField('Birth Date', validators=[InputRequired()])
    car_model = StringField('Car Model', validators=[InputRequired()])
    car_plate = StringField('Car Plate', validators=[InputRequired()])
    car_ride = StringField('Car Ride', validators=[InputRequired()])
    phone_number = StringField('Phone Number', validators=[InputRequired()])
    submit = SubmitField('Submit')




# Create the login form
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=80)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=120)])
    submit = SubmitField('Log In')

# ---------------------------------------------------------- Authentication ---------------------------------------------------------------------


@app.route('/signup_user', methods=['GET', 'POST'])
def signup_user():
    form = UserRegistrationForm()
    if form.validate_on_submit():
        name = form.name.data
        lastname = form.lastname.data
        birthdate = form.birthdate.data
        username = form.username.data
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        cursor_users = get_db_users().cursor()
        cursor_users.execute("INSERT INTO users (name, lastname, birthdate, username, password) VALUES (?, ?, ?, ?, ?)",
                             (name, lastname, birthdate, username, hashed_password))
        get_db_users().commit()
        
        flash('User registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('auth/signup_user.html', form=form)



@app.route('/signup_driver', methods=['GET', 'POST'])
def signup_driver():
    form = DriverRegistrationForm()
    if form.validate_on_submit():
        name = form.name.data
        lastname = form.lastname.data
        username = form.username.data
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        cursor_drivers = get_db_drivers().cursor()
        cursor_drivers.execute("INSERT INTO drivers (name, lastname, username, password) VALUES (?, ?, ?, ?)",
                               (name, lastname, username, hashed_password))
        get_db_drivers().commit()
        
        flash('Driver registration successful!', 'success')
        return redirect(url_for('driver_info',username=username))
    return render_template('auth/signup_driver.html', form=form)


# New route to gather additional driver information after registration
@app.route('/driver_info/<username>', methods=['GET', 'POST'])
def driver_info(username):
    form = DriverInfoForm()
    if form.validate_on_submit():
        name = form.name.data
        lastname = form.lastname.data
        birthdate = form.birthdate.data
        car_model = form.car_model.data
        car_plate = form.car_plate.data
        car_ride = form.car_ride.data
        phone_number = form.phone_number.data

        # Store the collected information in MongoDB
        driver_info = {
            'username': username,
            'name': name,
            'lastname': lastname,
            'birthdate': birthdate,
            'car_model': car_model,
            'car_plate': car_plate,
            'car_ride': car_ride,
            'phone_number': phone_number,
        }
        
        collection_drivers_data.insert_one(driver_info)

        flash('Driver information saved successfully!', 'success')
        return redirect(url_for('login'))  

    return render_template('view/driver_info.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # Check if the user exists in the users table
        cursor_users = get_db_users().cursor()
        cursor_users.execute("SELECT * FROM users WHERE username = ?", (username,))
        user_data = cursor_users.fetchone()

        # Check if the user exists in the drivers table if not found in users table
        if not user_data:
            cursor_drivers = get_db_drivers().cursor()
            cursor_drivers.execute("SELECT * FROM drivers WHERE username = ?", (username,))
            driver_data = cursor_drivers.fetchone()

            if driver_data:
                # Verify password for driver
                if bcrypt.check_password_hash(driver_data[4], password):
                    driver = User(driver_data[0], driver_data[3])  # Create a User object for driver
                    login_user(driver)  # Log in the driver
                    return redirect(url_for('main_driver'))
                else:
                    flash('Invalid username or password', 'danger')
                    return redirect(url_for('home'))  # Redirect to home page if authentication fails
            
            flash('Invalid username or password', 'danger')
            return redirect(url_for('home'))  # Redirect to home page if authentication fails

        # Verify password for user
        if bcrypt.check_password_hash(user_data[5], password):
            user = User(user_data[0], user_data[4])  # Create a User object
            login_user(user)  # Log in the user
            return redirect(url_for('main_user'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('home'))  # Redirect to home page if authentication fails
    
    return render_template('auth/login.html', form=form)






@app.route('/logout')
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('home'))

# ------------------------------------view pages -------------------------------------------------------------

@app.route('/')
def home():
    return render_template('view/home.html')



# Here we have the map and pickup location......
@app.route('/main_user')
@login_required
def main_user():
    return render_template('view/main_user.html')




# When the user click on request driver it will execute this query to save their data 

@app.route('/save_data', methods=['POST'])
@login_required  
def save_data():
    if request.method == 'POST':
        data = request.json  

        # Incrementing order_id for each new order
        last_order = collection.find_one({}, sort=[('_id', -1)])  # Get the last order
        last_order_id = last_order['order_id'] if last_order else 0  # Get the last order_id

        # Increment the last order_id to generate a new order_id
        new_order_id = last_order_id + 1

        # Add the username and order_id to the data
        data['username'] = current_user.username  
        data['order_id'] = new_order_id
        data['order_status'] = 'searching'
        data['driver_username']= "" 

        # Store the data in MongoDB
        collection.insert_one(data)
        collection_orders_backup.insert_one(data)
        socketio.emit('join_room', {'room': str(new_order_id)})

        return jsonify({'order_id': new_order_id})  
    


    # When the user click request driver , i will get the order_id here 
@app.route('/redirect_to_waiting', methods=['GET', 'POST'])
@login_required
def redirect_to_waiting():
    # Get the order_id from the JSON data received in the POST request
    order_id = request.json.get('order_id')

    # Redirect to the waiting page with the order_id in the URL
    return redirect(url_for('waiting', order_id=order_id))



# I will get the order id of the user in this page 
@app.route('/waiting/<order_id>', methods=['GET'])
@login_required
def waiting(order_id):
    # Retrieve the order details from the MongoDB using the order_id
    order_details = collection.find_one({'order_id': int(order_id)})

    if order_details:
        # Pass the order details to the waiting.html template
        return render_template('view/waiting.html', order_details=order_details)
    else:
        # Handle the case where the order details are not found
        return render_template('view/error.html', message='Order details not found')






# Orders will be shown on the drivers page with their id and evrything 
@app.route('/main_driver')
@login_required
def main_driver():
    
    # Check if the current user is a driver
    if current_user.is_authenticated:
        # Get driver's username
        driver_username = current_user.username
        
        # Retrieve driver's specific data from MongoDB based on the driver's username
        driver_data = collection_drivers_data.find_one({'username': driver_username})

        if driver_data:
            car_ride = driver_data.get('car_ride')  # Assuming 'car_ride' is a field in drivers_data collection
            
            # Retrieve orders matching the driver's 'car_ride' from user orders in MongoDB
            matching_orders = collection.find({'car_ride': car_ride})

            # Prepare a list to store formatted order details with user information
            orders_list = []

            # Iterate through matching orders and retrieve user details from 'user' collection
            for order in matching_orders:
                # Retrieve user details from 'user' collection based on username in the order
                user_details = collection.find_one({'username': order['username']})

                if user_details:
                    # Convert ObjectId to a string for JSON serialization
                    user_details['_id'] = str(user_details['_id'])

                    # Customize the data to be sent back (add more fields as needed)
                    formatted_order = {
                        'pickup_location': order.get('pickup_location'),
                        'dropoff_location':order.get('dropoff_location'),
                        'pickup_time':order.get('pickup_time'),
                        'username': order.get('username'),
                        'payment_method': order.get('payment_method'),
                        'order_id':order.get('order_id'),
                        'order_status':order.get('order_status')
                        
                    }
                    orders_list.append(formatted_order)
    
    return render_template('view/main_driver.html', matching_orders_with_user_data=orders_list)






# when the driver trigger the accept button it will changed in the mongo from searching to assign with the driver username 

@app.route('/accept_order/<order_id>', methods=['POST'])
def accept_order(order_id):
    driver_username = current_user.username  # Get the driver's username from the current_user object

    # Update the order in the MongoDB collection
    order = collection.find_one_and_update(
        {'order_id': int(order_id)},
        {'$set': {
            'order_status': 'assigned',
            'driver_username': driver_username  # Assign the driver's username to the order
        }},
        return_document=True
    )

    if order:
        # Return success message or updated order details
        join_room(str(order_id))
        return jsonify({'message': 'Order assigned to driver', 'order': order})
    else:
        # Return an error message if the order is not found or not updated
        return jsonify({'error': 'Failed to update order status'}), 400
    


@app.route('/user_chat/<order_id>')
def user_chat(order_id):
    # Retrieve order data from the 'collection' based on the order_id
    order_data = collection.find_one({'order_id': int(order_id)})
    
    if order_data:
        driver_username = order_data.get('driver_username')

        if driver_username:
            # Retrieve driver details from 'collection_drivers_data' based on driver_username
            driver_data = collection_drivers_data.find_one({'username': driver_username})

            if driver_data:
                # Get the order_status from the order_data
                order_status = order_data.get('order_status')

                # Pass all retrieved data to the template
                return render_template('view/user_chat.html', order_data=order_data, driver_data=driver_data, order_status=order_status)
    
    # Handle the case where driver or order data is not found
    return render_template('view/error.html', message='Data not found')



@app.route('/driver_chat/<order_id>')
def driver_chat(order_id):
    # Retrieve data from MongoDB based on order_id
    order_data = collection.find_one({'order_id': int(order_id)})
    print(order_data)
    
    if order_data:
        # Pass the retrieved order data to the template
        return render_template('view/driver_chat.html', order_data=order_data)
    else:
        # Handle the case where the order data is not found
        return render_template('view/error.html', message='Order details not found')








@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)  # Join the room based on the received room information


@socketio.on('user_message')
def handle_user_message(data):
    room = data.get('room')  # Extract the 'room' information
    message = data.get('message')

    if room:
        # Broadcast the received message to everyone in the room
        emit('receive_message', {'message': message}, room=room)
    else:
        # Handle the case when 'room' information is missing
        print("Room information missing in user_message event.")

@socketio.on('driver_message')
def handle_driver_message(data):
    room = data.get('room')  # Extract the 'room' information
    message = data.get('message')

    if room:
        # Broadcast the received message to everyone in the room
        emit('receive_message', {'message': message}, room=room)
    else:
        # Handle the case when 'room' information is missing
        print("Room information missing in driver_message event.")

# Function to emit the order ID to the respective chat sessions
def emit_order_id(order_id, room):
    socketio.emit('receive_order_id', {'order_id': order_id}, room=room)







@app.route('/complete_order/<order_id>', methods=['POST'])
def complete_order(order_id):
    
    # Update the order status to 'completed'
    result = collection.update_one({'order_id': int(order_id)}, {'$set': {'order_status': 'completed'}})

    if result.modified_count > 0:
        return jsonify({'message': 'Order marked as completed'})
    else:
        return jsonify({'error': 'Failed to mark order as completed'}), 400
    


if __name__ == '__main__':
    # app.run(port=8080,debug=True)
    socketio.run(app,port=8080,debug=True)

