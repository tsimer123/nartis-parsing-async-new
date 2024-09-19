import os

from dotenv import load_dotenv

load_dotenv()

DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')

# время ожидания статуса start для get_shedule в секундах
timeout_task = {
    'get_shedule': 1800,
    'get_leave_time': 1800,
    'get_tarif_mask': 1800,
    'set_leave_time': 3600,
    'set_tarif_mask': 3600,
    'set_shedule': 3600,
    'get_fw_meter': 1800,
}

# перечень команд для функции get_command
list_command = [
    'get_shedule',
    'get_leave_time',
    'get_tarif_mask',
    'get_fw_meter',
    'set_leave_time',
    'set_tarif_mask',
    'set_shedule',
]

list_command_after_set = [
    'set_tarif_mask',
    'set_shedule',
]

list_comannds_repeat = [
    'set_shedule',
]

count_repeat_conf = 4

# перечень возможных параметров для устаровки планировзика
list_shedule_param = ['archive daily', 'quality', 'load profile', 'no']

# интервал между запросами к БД при ожидании выполнения task
time_sleep_shedul_get_db = 20

# интервал актуальности true task
time_restart_true_task = 43200

# имя БД
db_name = 'sqlite_python_alchemy.db'
