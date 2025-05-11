# create the table
import json
import psycopg2
import psycopg2.extras
import time
import hashlib

RECORD = {}

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

# create authorization table


def create_authorization_table(conn):
    # drop the table if it exists
    drop_tables(conn)

    # Create the authorization table if it doesn't exist
    create_table_query = """
        CREATE TABLE IF NOT EXISTS Author (
            user_id VARCHAR(255),
            access_token VARCHAR(255) NOT NULL,
            refresh_token VARCHAR(255) NOT NULL,
            created_at FLOAT NOT NULL
        )
    """
    create_table(conn, create_table_query)

    print("Author table created successfully.")

    # Insert sample records into the authorization table
    insert_query = """
        INSERT INTO Author (user_id, access_token, refresh_token, created_at)
        VALUES (%s, %s, %s, %s)
    """
    RECORD["authorization"] = []
    insert_authorization_record(
        conn, create_sample_authorization_record("Jason"), insert_query)
    insert_authorization_record(
        conn, create_sample_authorization_record("Sally"), insert_query)
    insert_authorization_record(
        conn, create_sample_authorization_record("John"), insert_query)


def create_sample_authorization_record(user_id):
    user_id = user_id
    access_token = hashlib.sha256(str(user_id).encode()).hexdigest()
    refresh_token = hashlib.sha256(str(user_id+"refresh").encode()).hexdigest()
    created_at = time.time()
    RECORD["authorization"].append({
        'user_id': user_id,
        'access_token': access_token,
        'refresh_token': refresh_token,
        'created_at': created_at
    })
    # return a dictionary record
    return {
        'user_id': user_id,
        'access_token': access_token,
        'refresh_token': refresh_token,
        'created_at': created_at
    }


def drop_tables(yb):
    try:
        with yb.cursor() as yb_cursor:
            yb_cursor.execute('DROP TABLE IF EXISTS Author')
            yb_cursor.execute('DROP TABLE IF EXISTS Record')
        yb.commit()
    except Exception as e:
        print("Exception while dropping tables")
        print(e)
        exit(1)


def insert_authorization_record(yb, record, insert_query):
    try:
        with yb.cursor() as yb_cursor:
            yb_cursor.execute(insert_query, (record['user_id'], record['access_token'],
                                             record['refresh_token'], record['created_at']))
        yb.commit()
    except Exception as e:
        print("Exception while inserting record into authorization table")
        print(e)
        exit(1)
    print(record)


def create_record_table(conn):
    # Create the record table if it doesn't exist
    create_table_query = """
        CREATE TABLE IF NOT EXISTS Record (
            user_id VARCHAR(255),
            type VARCHAR(255) NOT NULL,
            time FLOAT NOT NULL
        )
    """
    create_table(conn, create_table_query)

    print("Record table created successfully.")

    # Insert sample records into the record table
    insert_query = """
        INSERT INTO Record (user_id, type, time)
        VALUES (%s, %s, %s)
    """
    RECORD["record"] = []
    insert_record_record(
        conn, create_record_sample_record("Jason", "i"), insert_query)
    insert_record_record(
        conn, create_record_sample_record("Jason", "o"), insert_query)


def create_record_sample_record(user_id, type):
    RECORD["record"].append({
        'user_id': user_id,
        'type': type,
        'time': time.time()
    })
    return {
        'user_id': user_id,
        'type': type,
        'time': time.time()
    }


def insert_record_record(yb, record, insert_query):
    try:
        with yb.cursor() as yb_cursor:
            yb_cursor.execute(insert_query, (record['user_id'], record['type'],
                                             record['time']))
        yb.commit()
    except Exception as e:
        print("Exception while inserting record into authorization table")
        print(e)
        exit(1)
    print(record)


def create_log_table(conn):
    # Create the record table if it doesn't exist
    create_table_query = """
        CREATE TABLE IF NOT EXISTS Log (
            user_id VARCHAR(255),
            type VARCHAR(255) NOT NULL,
            time FLOAT NOT NULL,
            duration FLOAT NOT NULL
        )
    """
    create_table(conn, create_table_query)

    print("Log table created successfully.")

    # Insert sample records into the record table
    insert_query = """
        INSERT INTO Log (user_id, type, time, duration)
        VALUES (%s, %s, %s, %s)
    """
    RECORD["log"] = []
    insert_log_record(
        conn, create_log_sample_record("Jason", "absent", 3600*8), insert_query)
    insert_log_record(
        conn, create_log_sample_record("Jason", "late", 3600), insert_query)
    insert_log_record(
        conn, create_log_sample_record("Jason", "overtime", 7200), insert_query)


def create_log_sample_record(user_id, type, duration):
    RECORD["log"].append({
        'user_id': user_id,
        'type': type,
        'time': time.time(),
        'duration': duration
    })
    # return a dictionary record
    return {
        'user_id': user_id,
        'type': type,
        'time': time.time(),
        'duration': duration
    }


def insert_log_record(yb, record, insert_query):
    try:
        with yb.cursor() as yb_cursor:
            yb_cursor.execute(insert_query, (record['user_id'], record['type'],
                                             record['time'], record['duration']))
        yb.commit()
    except Exception as e:
        print("Exception while inserting record into authorization table")
        print(e)
        exit(1)
    print(record)


def create_salary_table(conn):
    # Create the record table if it doesn't exist
    create_table_query = """
        CREATE TABLE IF NOT EXISTS Salary (
            user_id VARCHAR(255),
            salary FLOAT NOT NULL
        )
    """
    create_table(conn, create_table_query)

    print("Salary table created successfully.")

    # Insert sample records into the record table
    insert_query = """
        INSERT INTO Salary (user_id, salary)
        VALUES (%s, %s)
    """
    RECORD["salary"] = []
    insert_salary_record(
        conn, create_salary_sample_record("Jason"), insert_query)


def create_salary_sample_record(user_id):
    RECORD["salary"].append({
        'user_id': user_id,
        'salary': 10000
    })

    return {
        'user_id': user_id,
        'salary': 10000
    }


def insert_salary_record(yb, record, insert_query):
    try:
        with yb.cursor() as yb_cursor:
            yb_cursor.execute(
                insert_query, (record['user_id'], record['salary']))
        yb.commit()
    except Exception as e:
        print("Exception while inserting record into Log table")
        print(e)
        exit(1)
    print(record)


def create_employee_account_table(conn):
    # Create the record table if it doesn't exist
    create_table_query = """
        CREATE TABLE IF NOT EXISTS EmployeeAccount (
            account VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL,
            boss_id VARCHAR(255) NOT NULL
        )
    """
    create_table(conn, create_table_query)

    print("EmployeeAccount table created successfully.")

    # Insert sample records into the record table
    insert_query = """
        INSERT INTO EmployeeAccount (account, password, boss_id)
        VALUES (%s, %s, %s)
    """
    RECORD["employee_account"] = []
    insert_employee_account_record(
        conn, create_employee_account_sample_record("Jason", "Sally"), insert_query)


def create_employee_account_sample_record(user_id, boss_id):
    RECORD["employee_account"].append({
        'account': user_id,
        'password': user_id,
        'boss_id': boss_id
    })

    return {
        'account': user_id,
        'password': user_id,
        'boss_id': boss_id
    }


def insert_employee_account_record(yb, record, insert_query):
    try:
        with yb.cursor() as yb_cursor:
            yb_cursor.execute(
                insert_query, (record['account'], record['password'], record['boss_id']))
        yb.commit()
    except Exception as e:
        print("Exception while inserting record into EmployeeAccount table")
        print(e)
        exit(1)
    print(record)


def create_boss_account_table(conn):
    # Create the record table if it doesn't exist
    create_table_query = """
        CREATE TABLE IF NOT EXISTS BossAccount (
            account VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    """
    create_table(conn, create_table_query)

    print("BossAccount table created successfully.")

    # Insert sample records into the record table
    insert_query = """
        INSERT INTO BossAccount (account, password)
        VALUES (%s, %s)
    """
    RECORD["boss_account"] = []
    insert_boss_account_record(
        conn, create_boss_account_sample_record("Sally"), insert_query)
    insert_boss_account_record(
        conn, create_boss_account_sample_record("John"), insert_query)


def create_boss_account_sample_record(user_id):
    RECORD["boss_account"].append({
        'account': user_id,
        'password': user_id
    })

    return {
        'account': user_id,
        'password': user_id
    }


def insert_boss_account_record(yb, record, insert_query):
    try:
        with yb.cursor() as yb_cursor:
            yb_cursor.execute(
                insert_query, (record['account'], record['password']))
        yb.commit()
    except Exception as e:
        print("Exception while inserting record into BossAccount table")
        print(e)
        exit(1)
    print(record)


def create_table(yb, create_table_query):
    try:
        with yb.cursor() as yb_cursor:
            yb_cursor.execute(create_table_query)
        yb.commit()
    except Exception as e:
        print("Exception while creating table in YugabyteDB")
        print(e)
        exit(1)


# test
if __name__ == "__main__":
    try:
        conn = psycopg2.connect(host=CONFIG['host'], port=CONFIG['port'], database=CONFIG['dbName'],
                                user=CONFIG['dbUser'], password=CONFIG['dbPassword'],
                                connect_timeout=10)

    except Exception as e:
        print("Exception while connecting to YugabyteDB")
        print(e)

    print(">>>> Successfully connected to YugabyteDB!")
    create_authorization_table(conn)
    create_record_table(conn)
    create_log_table(conn)
    create_salary_table(conn)
    create_employee_account_table(conn)
    create_boss_account_table(conn)
    print("Tables created successfully.")
    # Close the connection
    conn.close()
    # write the records to a json file
    with open('access_control_system/sample_record.json', 'w') as f:
        # clean the file
        f.truncate(0)
        # write the records to the file
        json.dump(RECORD, f, indent=4)
