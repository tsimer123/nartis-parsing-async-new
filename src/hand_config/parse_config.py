from os import path

import yaml


def get_data() -> dict | None:
    file_path = 'config.yml'
    if path.isfile(file_path) is True:
        with open(file_path) as file:
            date = yaml.safe_load(file)
            return date
    else:
        return None


def get_count_repeat_conf() -> int | None:
    result = get_data()
    if result is not None:
        if 'request' in result and 'count_repeat_conf' in result['request']:
            if type(result['request']['count_repeat_conf']) is int:
                return result['request']['count_repeat_conf']
            else:
                return None
        else:
            return None
    else:
        return None


def get_time_sleep_shedul_get_db() -> int | None:
    result = get_data()
    if result is not None:
        if 'request' in result and 'time_sleep_shedul_get_db' in result['request']:
            if type(result['request']['time_sleep_shedul_get_db']) is int:
                return result['request']['time_sleep_shedul_get_db']
            else:
                return None
        else:
            return None
    else:
        return None


def get_time_restart_true_task() -> int | None:
    result = get_data()
    if result is not None:
        if 'request' in result and 'time_restart_true_task' in result['request']:
            if type(result['request']['time_restart_true_task']) is int:
                return result['request']['time_restart_true_task']
            else:
                return None
        else:
            return None
    else:
        return None


def get_db_name() -> str | None:
    result = get_data()
    if result is not None:
        if 'db' in result and 'db_name' in result['db']:
            if type(result['db']['db_name']) is str:
                return result['db']['db_name']
            else:
                return None
        else:
            return None
    else:
        return None


def get_wl_del_name() -> str | None:
    result = get_data()
    if result is not None:
        if 'doc' in result and 'wl_del_name' in result['doc']:
            if type(result['doc']['wl_del_name']) is str:
                return result['doc']['wl_del_name']
            else:
                return None
        else:
            return None
    else:
        return None
