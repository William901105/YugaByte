import psycopg2
import json

# read host name from host.json file
with open('access_control_system/url.json') as f:
    data = json.load(f)
    HOST = data['host']
    PORT = data['port']

CONFIG = {
    'host': HOST,
    'port': PORT,
    'dbName': 'yugabyte',
    'dbUser': 'yugabyte',
    'dbPassword': 'yugabyte',
    'sslMode': '',
    'sslRootCert': ''
}


def dump_database(target_file):
    data = {}
    # connect to the database
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

    # create a cursor
    cur = conn.cursor()

    # get data in authorization table
    cur.execute("SELECT * FROM  author")
    auth_data = cur.fetchall()
    auth_columns = [desc[0] for desc in cur.description]
    auth_data_dict = [dict(zip(auth_columns, row)) for row in auth_data]
    data['author'] = auth_data_dict

    # get data in record table
    cur.execute("SELECT * FROM record")
    record_data = cur.fetchall()
    record_columns = [desc[0] for desc in cur.description]
    record_data_dict = [dict(zip(record_columns, row)) for row in record_data]
    data['record'] = record_data_dict

    # get data in log table
    cur.execute("SELECT * FROM log")
    log_data = cur.fetchall()
    log_columns = [desc[0] for desc in cur.description]
    log_data_dict = [dict(zip(log_columns, row)) for row in log_data]
    data['log'] = log_data_dict

    # get data in salary table
    cur.execute("SELECT * FROM salary")
    salary_data = cur.fetchall()
    salary_columns = [desc[0] for desc in cur.description]
    salary_data_dict = [dict(zip(salary_columns, row)) for row in salary_data]
    data['salary'] = salary_data_dict

    # get data in employee_account table
    cur.execute("SELECT * FROM employeeaccount")
    employee_account_data = cur.fetchall()
    employee_account_columns = [desc[0] for desc in cur.description]
    employee_account_data_dict = [
        dict(zip(employee_account_columns, row)) for row in employee_account_data]
    data['employee_account'] = employee_account_data_dict

    # get data in boss_account table
    cur.execute("SELECT * FROM bossaccount")
    boss_account_data = cur.fetchall()
    boss_account_columns = [desc[0] for desc in cur.description]
    boss_account_data_dict = [
        dict(zip(boss_account_columns, row)) for row in boss_account_data]
    data['boss_account'] = boss_account_data_dict

    # write data to file
    with open(target_file, 'w') as f:
        json.dump(data, f, indent=4)
    print(">>>> Successfully dumped database to file: ", target_file)


# run the function
if __name__ == "__main__":
    dump_database('access_control_system/dump_database.json')
