chcp 65001
python ./access_control_system/create_database.py
start cmd /k "python ./access_control_system/api.py"
start cmd /k "timeout 5&&python ./access_control_system/access_control_system.py"
start cmd /k "timeout 5&&python ./access_control_system/salary.py"