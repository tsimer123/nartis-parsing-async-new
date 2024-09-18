import re
from datetime import datetime, timedelta

from data_class.data_get_command import MeterWlModel


def parser_response(meter: MeterWlModel, type_task: str, time_zone: int) -> MeterWlModel:
    if type_task == 'get_shedule':
        meter = parser_response_get_shedule(meter, time_zone)
    if type_task == 'get_leave_time' or type_task == 'set_leave_time':
        meter = parser_response_get_leave_time(meter, time_zone)
    if type_task == 'get_tarif_mask':
        meter = parser_response_get_tarif_mask(meter, time_zone)
    if type_task == 'get_fw_meter':
        meter = parser_response_get_fw_meter(meter, time_zone)
    if type_task == 'set_shedule':
        meter = parser_response_set_shedule(meter)
    if type_task == 'set_tarif_mask':
        meter = parser_response_set_tarif_mask(meter)
    return meter


def parser_response_get_shedule(meter: MeterWlModel, time_zone: int) -> MeterWlModel:
    """парсим результат запроса планировщка для формирования записи в БД"""
    try:
        if meter.task_hand_log.response is not None:
            if 'schedule' in meter.task_hand_log.response:
                if meter.task_hand_log.response['schedule'] is not None:
                    if 'task' in meter.task_hand_log.response['schedule']:
                        shedule_src: str = meter.task_hand_log.response['schedule'][1:-1]
                        shedule_src = shedule_src.split(';')
                        if len(shedule_src) == 4:
                            dict_shedule = {}
                            count_ss = 0
                            for line_ss in shedule_src:
                                task_name = f'task_{count_ss}'
                                temp_task = parse_task_shed(line_ss)
                                if temp_task is not False:
                                    dict_shedule[task_name] = temp_task
                                else:
                                    meter.schedule_status = 'invalid'
                                    break
                                count_ss += 1
                            if 'task_3' in [key for key in dict_shedule]:
                                meter.schedule = dict_shedule
                                datetime_object = str_to_date(meter.task_hand_log.response['time'])
                                meter.schedule_date = datetime_object + timedelta(hours=time_zone)
                                meter.schedule_status = 'valid'
                            else:
                                meter.schedule_status = 'invalid'
                        else:
                            meter.schedule_status = 'invalid'
                    else:
                        meter.schedule_status = 'invalid'
                else:
                    meter.schedule_status = 'invalid'
            else:
                meter.schedule_status = 'invalid'
        else:
            meter.schedule_status = 'invalid'
    except Exception as ex:
        print(ex.args)
    return meter


def parse_task_shed(str_task: str) -> dict | bool:
    task_dict = {
        'type': 'NotInit',
        'day': 'NotInit',
        'time': 'NotInit',
    }

    position = str_task.find(':')
    task_list = str_task[position:].split(',')
    task_dict['type'] = task_list[0].lstrip().replace(': type: ', '')
    task_dict['day'] = task_list[1].lstrip().replace('day: ', '')
    task_dict['time'] = task_list[2].lstrip().replace('time: ', '')

    for value in task_dict.values():
        if value == 'NotInit':
            return False

    return task_dict


def parser_response_get_tarif_mask(meter: MeterWlModel, time_zone: int) -> MeterWlModel:
    """парсим результат запроса тарифной маски для формирования записи в БД"""
    if meter.task_hand_log.response is not None:
        if 'tariff_mask' in meter.task_hand_log.response:
            if meter.task_hand_log.response['tariff_mask'] is not None:
                meter.tariff_mask = meter.task_hand_log.response['tariff_mask']
                datetime_object = str_to_date(meter.task_hand_log.response['time'])
                meter.tariff_mask_date = datetime_object + timedelta(hours=time_zone)
                meter.tariff_mask_status = 'valid'
            else:
                meter.tariff_mask_status = 'invalid'
        else:
            meter.tariff_mask_status = 'invalid'
    else:
        meter.tariff_mask_status = 'invalid'
    return meter


def parser_response_get_leave_time(meter: MeterWlModel, time_zone: int) -> MeterWlModel:
    """парсим результат запроса времени выыхода из сети для формирования записи в БД"""
    if meter.task_hand_log.response is not None:
        if 'leave_time' in meter.task_hand_log.response:
            if meter.task_hand_log.response['leave_time'] is not None:
                meter.leave_time = meter.task_hand_log.response['leave_time']
                datetime_object = str_to_date(meter.task_hand_log.response['time'])
                meter.leave_time_date = datetime_object + timedelta(hours=time_zone)
                meter.leave_time_status = 'valid'
            else:
                meter.leave_time_status = 'invalid'
        else:
            meter.leave_time_status = 'invalid'
    else:
        meter.leave_time_status = 'invalid'
    return meter


def parser_response_get_fw_meter(meter: MeterWlModel, time_zone: int) -> MeterWlModel:
    if meter.task_hand_log.response is not None:
        if 'version' in meter.task_hand_log.response:
            if meter.task_hand_log.response['version'] is not None:
                version = split_meter_board_vers(meter.task_hand_log.response['version'])
                if version is not None:
                    datetime_object = str_to_date(meter.task_hand_log.response['time'])
                    meter.board_ver = version['board_ver']
                    meter.board_ver_date = datetime_object + timedelta(hours=time_zone)
                    meter.board_ver_status = 'valid'
                    meter.fw_meter = version['fw_meter']
                    meter.fw_meter_date = datetime_object + timedelta(hours=time_zone)
                    meter.fw_meter_status = 'valid'
                else:
                    meter.board_ver_status = 'invalid'
                    meter.fw_meter_status = 'invalid'
            else:
                meter.board_ver_status = 'invalid'
                meter.fw_meter_status = 'invalid'
        else:
            meter.board_ver_status = 'invalid'
            meter.fw_meter_status = 'invalid'
    else:
        meter.board_ver_status = 'invalid'
        meter.fw_meter_status = 'invalid'
    return meter


def split_meter_board_vers(version: str) -> dict | None:
    # "hwName=UNIV.049-05[13], swVersion=1.88"
    # "hwName=6477.049-04[8]�, swVersion=1.69"

    dict_version = {
        'board_ver': None,
        'fw_meter': None,
    }

    if 'hwName' in version:
        list_temp = version.split(',')
        dict_version['board_ver'] = list_temp[0].replace('hwName=', '').strip()
        if len(list_temp) == 2:
            if 'swVersion' in list_temp[1]:
                dict_version['fw_meter'] = list_temp[1].replace('swVersion=', '').strip()
                if dict_version['board_ver'][-1] != ']':
                    dict_version['board_ver'] = dict_version['board_ver'][:-1]
                return dict_version
            else:
                return dict_version
        else:
            return None
    else:
        if re.fullmatch('^([0-9]{1})\.([0-9]{1,3})', version) is not None:
            dict_version['fw_meter'] = version
            return dict_version
        else:
            return None


def parser_response_set_shedule(meter: MeterWlModel) -> MeterWlModel:
    """парсим результат устанолвки планировщика для формирования записи в БД"""
    if meter.task_hand_log.response is not None:
        if meter.task_hand_log.status_task_db == 'true':
            meter.set_schedule_date = datetime.now()
            meter.set_schedule_status = 'valid'
        else:
            meter.set_schedule_status = 'invalid'
    else:
        meter.set_schedule_status = 'invalid'
    return meter


def parser_response_set_tarif_mask(meter: MeterWlModel) -> MeterWlModel:
    """парсим результат устанолвки планировщика для формирования записи в БД"""
    if meter.task_hand_log.response is not None:
        if meter.task_hand_log.status_task_db == 'true':
            meter.set_tariff_mask_date = datetime.now()
            meter.set_tariff_mask_status = 'valid'
        else:
            meter.set_tariff_mask_status = 'invalid'
    else:
        meter.set_tariff_mask_status = 'invalid'
    return meter


def str_to_date(date_res: str) -> datetime:
    return datetime.strptime(date_res, '%Y-%m-%d %H:%M:%S.%f')
