import json
host = "0.tcp.jp.ngrok.io"
port = "5432"

# write the URL to url.json and backup_url.json
url_data = {"host": host, "port": port}
with open("access_control_system/url.json", 'w') as file:
    json.dump(url_data, file, indent=4)
