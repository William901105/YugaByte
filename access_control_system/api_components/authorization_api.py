# authorizatin_api.py
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import time
import hashlib

# read host name from host.json file
with open('access_control_system/url.json') as f:
    data = json.load(f)
    HOST = data['host']
    PORT = data['port']

# configurations for database connection
CONFIG = {
    'host': HOST,
    'port': PORT,
    'dbName': 'yugabyte',
    'dbUser': 'yugabyte',
    'dbPassword': 'yugabyte',
    'sslMode': '',
    'sslRootCert': ''
}


def authorization(access_token, user_id):  # authirization main function
    # Connect to the database
    try:
        if CONFIG['sslMode'] != '':
            conn = psycopg2.connect(host=CONFIG['host'], port=CONFIG['port'], database=CONFIG['dbName'],
                                    user=CONFIG['dbUser'], password=CONFIG['dbPassword'],
                                    sslmode=CONFIG['sslMode'], sslrootcert=CONFIG['sslRootCert'],
                                    connect_timeout=10)
        else:
            conn = psycopg2.connect(host=CONFIG['host'], port=CONFIG['port'], database=CONFIG['dbName'],
                                    user=CONFIG['dbUser'], password=CONFIG['dbPassword'],
                                    connect_timeout=10)

    except Exception as e:
        print("Exception while connecting to YugabyteDB")
        print(e)
        return None

    print(">>>> Successfully connected to YugabyteDB!")

    # Create a cursor object using the connection
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Execute a query to check if the access token is valid for the given user ID
    query = """
        SELECT * FROM Author WHERE access_token = %s AND user_id = %s
    """
    cursor.execute(query, (access_token, user_id))

    # Fetch the result of the query
    result = cursor.fetchone()

    # check if the result is none
    if result is None:
        print("Access token is invalid.")
        # Close the cursor and connection
        cursor.close()
        conn.close()
        return "Invalid"

    # get the current time and date
    current_time = time.time()

    # get the time from the result
    token_time = result[3]  # the time is in the forth column

    # check if the token is expired
    if current_time - token_time > 3600:  # 1 hour expiration time
        print("Access token is expired.")
        # Close the cursor and connection
        cursor.close()
        conn.close()
        return "Expired"

    # Close the cursor and connection
    cursor.close()
    conn.close()
    print("Access token is valid.")
    return "Valid"


def update_token(refresh_token, user_id):  # update the token function
    # Connect to the database
    try:
        if CONFIG['sslMode'] != '':
            conn = psycopg2.connect(host=CONFIG['host'], port=CONFIG['port'], database=CONFIG['dbName'],
                                    user=CONFIG['dbUser'], password=CONFIG['dbPassword'],
                                    sslmode=CONFIG['sslMode'], sslrootcert=CONFIG['sslRootCert'],
                                    connect_timeout=10)
        else:
            conn = psycopg2.connect(host=CONFIG['host'], port=CONFIG['port'], database=CONFIG['dbName'],
                                    user=CONFIG['dbUser'], password=CONFIG['dbPassword'],
                                    connect_timeout=10)

    except Exception as e:
        print("Exception while connecting to YugabyteDB")
        print(e)
        return None

    print(">>>> Successfully connected to YugabyteDB!")

    # Create a cursor object using the connection
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # check if the refresh token is valid for the given user ID
    query = """
        SELECT * FROM Author WHERE refresh_token = %s AND user_id = %s
    """
    cursor.execute(query, (refresh_token, user_id))

    # Fetch the result of the query
    result = cursor.fetchone()

    # check if the result is none
    if result is None:
        print("Refresh token is invalid.")
        # Close the cursor and connection
        cursor.close()
        conn.close()
        return None

    # create a new access token and refresh token
    new_access_token = hashlib.sha256(
        (str(result[1]) + str(time.time())).encode()).hexdigest()
    new_refresh_token = hashlib.sha256(
        (str(result[2]) + str(time.time())).encode()).hexdigest()

    # update the access token and refresh token in the database
    update_query = """
        UPDATE Author SET access_token = %s, refresh_token = %s, created_at = %s WHERE user_id = %s
    """
    cursor.execute(update_query, (new_access_token,
                   new_refresh_token, time.time(), user_id))
    conn.commit()

    # Close the cursor and connection
    cursor.close()
    conn.close()
    print("Access token and refresh token updated successfully.")
    return {"new_access_token": new_access_token, "new_refresh_token": new_refresh_token}


# run the app
app = Flask(__name__)
CORS(app)


@app.route('/authorization/authorize', methods=['GET'])
def run_authorization():
    data = request.get_json()
    access_token = data['access_token']
    user_id = data['user_id']

    result = authorization(access_token, user_id)
    if result == "Invalid":
        return jsonify({"result": "Invalid"}), 401
    elif result == "Expired":
        return jsonify({"result": "Expired"}), 401
    else:
        return jsonify({"result": "Valid"}), 200


@app.route('/authorization/refreshToken', methods=['POST'])
def run_update_token():
    data = request.get_json()
    refresh_token = data['refresh_token']
    user_id = data['user_id']

    result = update_token(refresh_token, user_id)
    if result == None:
        return jsonify({"result": "Invalid"}), 401
    else:
        return jsonify(result), 200


# test
if __name__ == "__main__":
    # run the app on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
