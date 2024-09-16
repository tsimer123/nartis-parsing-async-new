from datetime import datetime, timedelta

from data_class.data_get_command import ListTaskModel, MeterWlModel


def parser_response(meter: MeterWlModel, type_task: str, time_zone: int) -> MeterWlModel:
    if type_task == 'get_shedule':
        meter = parser_response_get_shedule(meter, time_zone)
    if type_task == 'get_leave_time' or type_task == 'set_leave_time':
        meter = parser_response_get_leave_time(meter, time_zone)
    if type_task == 'get_tarif_mask':
        meter = parser_response_get_tarif_mask(meter, time_zone)
    return meter


def parser_response_get_shedule(meter: MeterWlModel, time_zone: int) -> ListTaskModel:
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


def parser_response_get_tarif_mask(meter: MeterWlModel, time_zone: int) -> ListTaskModel:
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


def parser_response_get_leave_time(meter: MeterWlModel, time_zone: int) -> ListTaskModel:
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


def str_to_date(date_res: str) -> datetime:
    return datetime.strptime(date_res, '%Y-%m-%d %H:%M:%S.%f')
