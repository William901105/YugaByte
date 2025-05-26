import json

blank_data = {"access_token": None,
              "refresh_token": None, "user_id": None, "role": None}

# write the blank data to a boss_session.json and employee_session.json file


def write_blank_data(file_path):
    with open(file_path, 'w') as file:
        json.dump(blank_data, file, indent=4)


write_blank_data("access_control_system/boss_session.json")
write_blank_data("access_control_system/employee_session.json")

# set the database URL to url.json and backup_url.json


def set_database_url():
    # read the URL from keyboard input
    # default host is 0.tcp.jp.ngrok.io
    host = input(
        "Enter the main database host (default: 0.tcp.jp.ngrok.io): ") or "0.tcp.jp.ngrok.io"
    port = input("Enter the main database port: ")

    # write the URL to url.json and backup_url.json
    url_data = {"host": host, "port": port}
    with open("access_control_system/url.json", 'w') as file:
        json.dump(url_data, file, indent=4)

    host = input(
        "Enter the backup database host (default: 0.tcp.jp.ngrok.io): ") or "0.tcp.jp.ngrok.io"
    port = input("Enter the backup database port: ")
    backup_url_data = {"host": host, "port": port}
    with open("access_control_system/backup_url.json", 'w') as file:
        json.dump(backup_url_data, file, indent=4)


set_database_url()
