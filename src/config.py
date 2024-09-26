import os

from dotenv import load_dotenv

from hand_config.parse_config import (
    get_count_repeat_conf,
    get_db_name,
    get_time_restart_true_task,
    get_time_sleep_shedul_get_db,
)

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
    'get_set_tarif_mask': 1800,
    'get_set_shedule': 1800,
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

# перечень возможных параметров для устаровки планировзика
list_shedule_param = ['archive daily', 'quality', 'load profile', 'no']


# количество повторов для list_comannds_repeat + 1, по умолчанию 5
_count_repeat_conf = get_count_repeat_conf()
count_repeat_conf = _count_repeat_conf if _count_repeat_conf is not None else 5

# интервал между запросами к БД при ожидании выполнения task
_time_sleep_shedul_get_db = get_time_sleep_shedul_get_db()
time_sleep_shedul_get_db = _time_sleep_shedul_get_db if _time_sleep_shedul_get_db is not None else 20

# интервал актуальности true task
_time_restart_true_task = get_time_restart_true_task()
time_restart_true_task = _time_restart_true_task if _time_restart_true_task is not None else 43200

# имя БД
_db_name = get_db_name()
db_name = _db_name if _db_name is not None else 'sqlite_python_alchemy.db'
