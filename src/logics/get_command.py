import json
import re
from asyncio import sleep
from datetime import datetime

from aiohttp import ClientSession, CookieJar

from base_http.base import BaseRequest
from config import time_sleep_shedul_get_db
from data_class.data_get_command import (
    EquipmentInfoModel,
    GetComandModel,
    GetResultTaskModel,
    ListTaskModel,
    MeterWlAllModel,
    MeterWlModel,
    StatusHandModel,
    TaskGetModel,
)
from data_class.data_get_db import TaskFromDbkModel
from logics.get_db import get_db_task
from logics.parse_get_comman import parser_response
from sql.model import TaskEquipmentHandlerModelGet


async def get_command(task_rb: TaskEquipmentHandlerModelGet) -> GetComandModel:
    start_time = datetime.now()
    print(
        f'{datetime.now()}: start get data for task {task_rb.task_id}, equipment {task_rb.serial_in_sourse}, command: {task_rb.type_task}'
    )
    result = GetComandModel(
        task_id=task_rb.task_id,
        equipment_id=task_rb.equipment_id,
        type_task=task_rb.type_task,
        status_task='false',
        meter_true=task_rb.meter_true,
    )
    # включаем хранение куки для ip адресов
    cookiejar = CookieJar(unsafe=True)
    # создаем список ip адресов УСПД
    list_ip = [task_rb.ip1]
    if task_rb.ip2 is not None:
        list_ip.append(task_rb.ip2)
    # создаем подключени
    async with ClientSession(cookie_jar=cookiejar) as session:
        # пытаемся подключится к УСПД
        for ip in list_ip:
            con = BaseRequest(
                session,
                ip,
                task_rb.login,
                task_rb.passw,
            )
            # получаем токен авторизации
            auth = await con.get_auth()
            if auth.status is True:
                break
        if auth.status is True:
            token = auth.data
            try:
                # полуячаем данные по УСПД
                result.equipment_info = await get_dev_info(con, token)
                # получаем БС из УСПД
                result.meter_wl = await get_wl(con, token)
                if result.meter_wl is not None:
                    if result.meter_wl.status is True:
                        if len(result.meter_wl.meter_wl) > 0:
                            # получаем id ПУ из БС для запросов параметров
                            id_for_task = get_meters_for_task(task_rb.meter_true, result.meter_wl.meter_wl)
                            if len(id_for_task) > 0:
                                list_task = []
                                # создаем таски по параметрам
                                count_break = 0
                                for line_id in id_for_task:
                                    await sleep(1)
                                    task_id = await hand_command(
                                        task_rb.type_task, con, token, line_id, task_rb.param_data
                                    )
                                    # task_id, meter_id, true/false/wait, status_hand, error
                                    list_task.append(
                                        ListTaskModel(
                                            task_id=task_id.task_id,
                                        )
                                    )
                                    # добавляем результат создание таски на УСПД в ПУ
                                    result = append_response_task_in_meter(result, line_id, task_id)
                                    print(
                                        f'Equipment {task_rb.serial_in_sourse}, task_in {task_rb.task_id} task {task_id.task_id}'
                                    )
                                    # if count_break > 9:
                                    #     break
                                    count_break += 1
                                    # [task_id.task_id, '', 'wait', {}, False, '']
                                if len(list_task) > 0:
                                    result_task = await hand_task_db(ip, list_task, con, token)
                                    # добавляем результат обработки таски в ПУ
                                    if len(result_task.list_task) > 0:
                                        # добавляем лог обработанных тасок
                                        result = append_handler_task_in_meter(result, result_task)
                                        # удялем из списка ПУ если по ним не делали таски
                                        result = del_true_meter_from_bd(result, id_for_task)
                                        # парсим результаты тасок и записываем в ПУ
                                        result = parse_result_task(result, task_rb.time_zone)
                                    if result_task.error is not None:
                                        result.error = result_task.error
                                    if result_task.status is True:
                                        result.status_task = 'true'
                                else:
                                    result.error = 'Не создалось ни одной таски'
                            else:
                                result.status_task = 'true'
                                result.error = 'В БС нет ПУ отличных от meter_true'
                        else:
                            result.error = 'В БС нет ПУ'
                    else:
                        result.error = str(result.meter_wl.error)
                else:
                    result.error = 'Не предвиденная ошибка: meter_wl = None'

            except Exception as ex:
                result.error = str(ex.args)
        else:
            result.error = str(auth.error)

    end_time = datetime.now()
    delta = end_time - start_time
    result.total_time = round(delta.total_seconds())
    print(
        f'{datetime.now()}: stop get data for task {task_rb.task_id}, equipment {task_rb.serial_in_sourse}, command: {task_rb.type_task}, total time {result.total_time}'
    )

    return result


async def get_dev_info(con: BaseRequest, token: str) -> EquipmentInfoModel | None:
    """Функция запропшивает информацию об УСПД, если вернет None, то это не штатная ситуация"""
    result = None
    equipment_info = await con.get_request('devinfo', token)
    date_now = datetime.now()
    try:
        if equipment_info.status is True:
            equipment_info.data = json.loads(equipment_info.data)
            result = EquipmentInfoModel(
                status=True,
                serial=equipment_info.data['serial'],
                fw_version=equipment_info.data['uspd_update_version'],
                type_equipment=equipment_info.data['name'],
                modification=equipment_info.data['modification'],
                date_response=date_now,
            )
        else:
            result = EquipmentInfoModel(status=False, error=str(equipment_info.error), date_response=date_now)
    except Exception as ex:
        result = EquipmentInfoModel(status=False, error=str(ex.args), date_response=date_now)
    return result


async def get_wl(con: BaseRequest, token: str) -> MeterWlAllModel | None:
    """Функция запропшивает ПУ из БС, если вернет None, то это не штатная ситуация"""
    result = None
    meter_wl = await con.get_request('devices', token)
    try:
        if meter_wl.status is True:
            result = MeterWlAllModel(status=True)
            meter_wl.data = json.loads(meter_wl.data)
            if len(meter_wl.data) > 0:
                result.meter_wl = []
                for line in meter_wl.data:
                    result.meter_wl.append(
                        MeterWlModel(
                            id_wl=line['id'],
                            eui=line['eui'],
                            archive=line['archive'],
                            included_in_survey=line['included_in_survey'],
                        )
                    )
        else:
            result = MeterWlAllModel(status=False, error=str(meter_wl.error))
    except Exception as ex:
        result = MeterWlAllModel(status=False, error=str(ex.args))

    return result


def get_meters_for_task(meter_true: str, meters_wl: list[MeterWlModel]) -> list[int] | None:
    """Функция готовит список id ПУ из БС для которых надо запросить информацию"""
    result = None
    if meter_true is not None:
        list_meters_true = set(meter_true.split(','))
        meter_wl_id = set([line.eui for line in meters_wl if re.search('[ABCDEFabcdef]', line.eui) is not None])
        dif_eui = meter_wl_id - list_meters_true
        dif_eui = list(dif_eui)
        result = []
        for line_wl in meters_wl:
            for line_de in dif_eui:
                if line_wl.eui == line_de:
                    result.append(line_wl.id_wl)
                    break
    else:
        result = [line.id_wl for line in meters_wl]
    return result


async def get_task(con: BaseRequest, token: str, data_payload: dict) -> TaskGetModel | None:
    """Функция делает запрос для формирования задачи на вычитку парамера по id ПУ"""
    result = None
    shedule_task = await con.post_request('get_meter_settings', token, data_payload)
    try:
        if shedule_task.status is True:
            shedule_task.data = json.loads(shedule_task.data)

            result = TaskGetModel(
                status=True,
                task_id=shedule_task.data['taskId'],
            )
        else:
            result = TaskGetModel(status=False, error=str(shedule_task.error))
    except Exception as ex:
        result = TaskGetModel(status=False, error=str(ex.args))
    return result


async def set_task(con: BaseRequest, token: str, data_payload: dict) -> TaskGetModel | None:
    """Функция делает запрос для формирования задачи на вычитку парамера по id ПУ"""
    result = None
    shedule_task = await con.post_request('set_meter_settings', token, data_payload)
    try:
        if shedule_task.status is True:
            shedule_task.data = json.loads(shedule_task.data)

            result = TaskGetModel(
                status=True,
                task_id=shedule_task.data['taskId'],
            )
        else:
            result = TaskGetModel(status=False, error=str(shedule_task.error))
    except Exception as ex:
        result = TaskGetModel(status=False, error=str(ex.args))
    return result


async def hand_command(command: str, con: BaseRequest, token: str, param: str, paramData: str) -> TaskGetModel | None:
    """Фунеция по запуску запроса на вычитку параметра ПУ по типу команды"""
    if command == 'get_shedule':
        data_payload = {'devId': param, 'taskParam': 'SCHEDULE'}
        result = await get_task(con, token, data_payload)

    if command == 'get_leave_time':
        data_payload = {'devId': param, 'taskParam': 'LEAVE_TIME'}
        result = await get_task(con, token, data_payload)

    if command == 'get_tarif_mask':
        data_payload = {'devId': param, 'taskParam': 'TARIFF_MASK'}
        result = await get_task(con, token, data_payload)

    if command == 'set_leave_time':
        data_payload = {'devId': param, 'taskParam': 'LEAVE_TIME', 'paramData': [paramData]}
        result = await set_task(con, token, data_payload)

    if command == 'set_tarif_mask':
        data_payload = {'devId': param, 'taskParam': 'TARIFF_MASK', 'paramData': [paramData]}
        result = await set_task(con, token, data_payload)

    if command == 'set_shedule':
        paramData = paramData.split(',')
        data_payload = {'devId': param, 'taskParam': 'SCHEDULE', 'paramData': paramData}
        result = await set_task(con, token, data_payload)

    return result


async def hand_task_db(ip: str, list_task_in: list[ListTaskModel], con: BaseRequest, token: str) -> StatusHandModel:
    result = StatusHandModel(list_task=list_task_in)

    count_iter = 0
    number_iter = 10
    try:
        while count_iter < number_iter:
            await sleep(time_sleep_shedul_get_db)
            # получаем таски из БД
            status_task = await get_db_task(ip)
            if status_task.status is True:
                # проверям статутс тасок в БД
                result.list_task = match_task(result.list_task, status_task.task)
                result.list_task = await get_meter_data(result.list_task, con, token)
                # считаем отработанные таски и если все готовы то выходим из цикла
                count_hand_task = counter_true_hand_task(result.list_task)
                if count_hand_task == len(result.list_task):
                    task_false = counter_false_task(result.list_task)
                    if task_false == 0:
                        result.status = True
                    break
            else:
                result.error = status_task.error
            count_iter += 1
    except Exception as ex:
        result.error = str(ex.args)
    return result


def match_task(list_task: list[ListTaskModel], status_task: list[TaskFromDbkModel]) -> list[ListTaskModel]:
    """функция проверяющая статутус выполнения тасок"""
    count_lt = 0
    len_list_task = len(list_task)
    while count_lt < len_list_task:
        for line_st in status_task:
            if list_task[count_lt].task_id == line_st.task_id:
                list_task[count_lt].meter_id = line_st.meter_id
                if line_st.status_task == 1:
                    list_task[count_lt].status_task_db = 'true'
                    break
                if line_st.status_task == 3:
                    list_task[count_lt].status_task_db = 'false'
                    list_task[count_lt].status_hand = True
                    break
        count_lt += 1
    return list_task


async def get_meter_data(list_task: list[ListTaskModel], con: BaseRequest, token: str) -> list[list]:
    """функция получает все параметры ПУ"""
    count_t = 0
    len_list_task = len(list_task)
    while count_t < len_list_task:
        if list_task[count_t].status_task_db == 'true' and list_task[count_t].status_hand is not True:
            params = f'meter={list_task[count_t].meter_id}'
            for i in range(1, 3, 1):
                meter_param = await get_task_result(con, token, params)
                if meter_param.status is True:
                    print(f'Длина meter_param.data: {len(meter_param.data)}')
                    if meter_param.data is not None:
                        # print(meter_param['data'])
                        list_task[count_t].response = meter_param.data
                        # проверить чтоб не приходили нулевые
                        list_task[count_t].status_hand = True
                        list_task[count_t].error = None
                        break
                    else:
                        list_task[count_t].error = 'Запрос параметров по успешной таски вернул None'
                else:
                    list_task[count_t].error = str(meter_param.error)
                print(f'iter: {i}')
                if list_task[count_t].response is None:
                    print(f'запрос по результатмм таски итер: {i}, рузультат {list_task[count_t].response}')
                print(f'iter: {i}')

        count_t += 1
    return list_task


async def get_task_result(con: BaseRequest, token: str, param: str) -> GetResultTaskModel | None:
    """Функция делает запрос для формирования задачи на вычитку парамера по id ПУ"""
    result = None
    result_task = await con.get_request_with_params('get_meter_settings', token, param)

    if result_task.status is True:
        result_task.data = json.loads(result_task.data)

        result = GetResultTaskModel(
            status=True,
            data=result_task.data,
        )
    else:
        result = GetResultTaskModel(status=False, error=str(result_task.error))
    return result


def counter_true_hand_task(list_task: list[ListTaskModel]) -> int:
    """функция считает отработанные таски"""
    count_true = 0
    for line in list_task:
        if line.status_hand:
            count_true += 1

    return count_true


def counter_false_task(list_task: list[ListTaskModel]) -> int:
    """функция считает неудачные таски"""
    count_true = 0
    for line in list_task:
        if line.status_task_db == 'false':
            count_true += 1

    return count_true


def append_response_task_in_meter(result: GetComandModel, line_id: int, task_id: TaskGetModel) -> GetComandModel:
    count_meter_wl = 0
    len_meter_wl = len(result.meter_wl.meter_wl)

    while count_meter_wl < len_meter_wl:
        if line_id == result.meter_wl.meter_wl[count_meter_wl].id_wl:
            result.meter_wl.meter_wl[count_meter_wl].task_log = task_id
            break
        count_meter_wl += 1

    return result


def append_handler_task_in_meter(result: GetComandModel, result_task: StatusHandModel) -> GetComandModel:
    count_meter_wl = 0
    len_meter_wl = len(result.meter_wl.meter_wl)

    while count_meter_wl < len_meter_wl:
        for line in result_task.list_task:
            if line.meter_id == result.meter_wl.meter_wl[count_meter_wl].id_wl:
                result.meter_wl.meter_wl[count_meter_wl].task_hand_log = line
                break
        count_meter_wl += 1

    return result


def parse_result_task(result: GetComandModel, time_zone: int) -> GetComandModel:
    count_meter = 0
    len_meter = len(result.meter_wl.meter_wl)
    while count_meter < len_meter:
        if result.meter_wl.meter_wl[count_meter].task_hand_log is not None:
            result.meter_wl.meter_wl[count_meter] = parser_response(
                result.meter_wl.meter_wl[count_meter], result.type_task, time_zone
            )
        count_meter += 1

    return result


def del_true_meter_from_bd(result: GetComandModel, id_for_task: list[int]) -> GetComandModel:
    """Функция удаляет из result.meter_wl.meter_wl ПУ, для которых не делались таски так как они были в meter_true"""
    if len(result.meter_wl.meter_wl) > len(id_for_task):
        meter_wl = []

        for line_id in id_for_task:
            for line_meter in result.meter_wl.meter_wl:
                if line_meter.id_wl == line_id:
                    meter_wl.append(line_meter)
                    break
        result.meter_wl.meter_wl = meter_wl

    return result
