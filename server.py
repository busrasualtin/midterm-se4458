from flask import Flask, jsonify, request, make_response
from flasgger import Swagger, swag_from
from config import get_connection

import jwt
import datetime

from functools import wraps

SECRET_KEY = "busra"

app = Flask(__name__)
swagger = Swagger(app, template_file='swagger_doc.yml')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'x-access-tokens' in request.headers:
            token = request.headers['x-access-tokens']

        if not token:
            return jsonify({'message': 'A valid token is missing'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = data['user']
        except:
            return jsonify({'message': 'Token is invalid'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

# Dummy route to authenticate user and return a token
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM busrasu.[User] WHERE usernameUser=?", (data['username'],))
    user = cursor.fetchone()

    conn.close()

    if user and user[3] == data['password']:
        token_payload = {
            'username': user[2],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }
        token = jwt.encode(token_payload, SECRET_KEY, algorithm="HS256")
        
        return jsonify({'token': token}), 200
    else:
        
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

# Endpoint to fetch data from Azure SQL database
@app.route('/users', methods=['GET'])
def get_users():
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        # Include the schema name in your query
        cursor.execute('SELECT * FROM busrasu.[User]')  # Use the correct schema.table format
        users = cursor.fetchall()
        conn.close()
        return jsonify({'users': users}), 200
    else:
        return jsonify({'error': 'Failed to establish connection to database'}), 500

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data or 'name' not in data:
        return make_response('Giriş bilgileri eksik!', 400)

    conn = get_connection()
    cursor = conn.cursor()

    # Assuming your user table has columns for usernameUser and passwordUser, adjust the query accordingly
    query = "INSERT INTO busrasu.[User] (nameUser, usernameUser, passwordUser) VALUES (?, ?, ?)"
    try:
        cursor.execute(query, (data['name'], data['username'], data['password']))
        conn.commit()
        conn.close()
        return jsonify({'message': 'User created successfully'}), 201
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': f'Failed to create user: {e}'}), 500
    

# Endpoint to delete a user from Azure SQL database
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM busrasu.[User] WHERE idUser = ?', (user_id,))
            conn.commit()
            conn.close()
            return jsonify({'message': 'User deleted successfully'}), 200
        except Exception as e:
            return jsonify({'error': f'Failed to delete user: {e}'}), 500
    else:
        return jsonify({'error': 'Failed to establish connection to database'}), 500

@app.route('/houses', methods=['GET'])
def get_houses():
    conn = get_connection()
    if conn:
        try:
            page = request.args.get('page', default=1, type=int)  # Get the page parameter from the request
            page_size = 10  # Define the number of records per page

            cursor = conn.cursor()

            # Calculate the offset based on the page and page_size
            offset = (page - 1) * page_size

            # SQL query with LIMIT and OFFSET clauses for pagination
            query = 'SELECT * FROM busrasu.House ORDER BY idHouse OFFSET ? ROWS FETCH NEXT ? ROWS ONLY'
            cursor.execute(query, (offset, page_size))
            houses = cursor.fetchall()

            conn.close()
            return jsonify({'houses': houses}), 200
        except Exception as e:
            return jsonify({'error': f'Failed to fetch houses: {e}'}), 500
    else:
        return jsonify({'error': 'Failed to establish connection to database'}), 500
    

@app.route('/bookings', methods=['GET'])
def get_bookings():
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM busrasu.Booking')  
        bookings = cursor.fetchall()
        conn.close()
        return jsonify({'bookings': bookings}), 200
    else:
        return jsonify({'error': 'Failed to establish connection to database'}), 500
    
def is_slot_available(availabilityStartBooking, availabilityEndBooking, cursor):
    cursor.execute('SELECT COUNT(*) FROM busrasu.Booking WHERE (availabilityStartBooking <= ? AND availabilityEndBooking >= ?) OR (availabilityStartBooking <= ? AND availabilityEndBooking >= ?)', (availabilityStartBooking, availabilityStartBooking, availabilityEndBooking, availabilityEndBooking))
    overlap_count = cursor.fetchone()[0]
    return overlap_count == 0

# Endpoint to create an appointment
@app.route('/createAppointment', methods=['POST'])
def create_appointment():
    data = request.get_json()

    conn = get_connection()
    cursor = conn.cursor()

    # Assuming your user table has columns for usernameUser and passwordUser, adjust the query accordingly
    query = "INSERT INTO busrasu.[Booking] (availabilityStartBooking, availabilityEndBooking, guestNumberBooking, User_idUser, House_idHouse) VALUES (?, ?, ?, ?, ?)"
    try:
        cursor.execute(query, (data['availabilityStartBooking'], data['availabilityEndBooking'], data['guestNumberBooking'], data['User_idUser'], data['House_idHouse']))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Booking created successfully'}), 201
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'error': f'Failed to create booking: {e}'}), 500


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
