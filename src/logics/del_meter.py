import json
from datetime import datetime

from aiohttp import ClientSession, CookieJar

from base_http.base import BaseRequest
from data_class.data_get_command import GetComandModel, MeterWlDelAllModel, MeterWlDelModel, MeterWlModel
from logics.general_func import get_dev_info, get_tzcode, get_wl
from sql.model import (
    TaskEquipmentHandlerModelGet,
)


async def set_del_meter_wl(task_rb: TaskEquipmentHandlerModelGet):
    start_time = datetime.now()
    print(
        f'{datetime.now()}: start set_del_meter_wl for task {task_rb.task_id}, equipment {task_rb.serial_in_sourse}, command: {task_rb.type_task}'
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
    # создаем подключение
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
                # получаем часовй пояс УСПД
                timezone = await get_tzcode(con, token)
                if timezone is not None:
                    task_rb.time_zone = timezone
                # получаем данные по УСПД
                result.equipment_info = await get_dev_info(con, token)
                # получаем БС из УСПД
                result.meter_wl = await get_wl(con, token)
                if result.meter_wl is not None:
                    if result.meter_wl.status is True:
                        if len(result.meter_wl.meter_wl) > 0:
                            # получаем id ПУ из БС для удаления
                            id_for_del = get_meters_for_task_all(task_rb, result)
                            if len(id_for_del) > 0:
                                result.meter_wl_del = await handler_delete_meter(
                                    con, token, id_for_del, task_rb, result.meter_wl.meter_wl
                                )
                                result.status_task = await check_all_del_meter(con, token, task_rb)
                            else:
                                result.status_task = 'true'
                                result.error = 'В БС нет ПУ для удаления'
                        else:
                            result.meter_wl_del = set_result_empty_wl(task_rb)
                            result.status_task = 'true'
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


def set_result_empty_wl(task_rb: TaskEquipmentHandlerModelGet) -> MeterWlDelAllModel:
    """Функция формирует данные по удаленным ПУ если БС пустой"""
    return MeterWlDelAllModel(empty_wl=True, list_meter_del=task_rb.param_data)


def get_meters_for_task_all(task_rb: TaskEquipmentHandlerModelGet, result_in: GetComandModel) -> list[int] | None:
    """Функция готовит список id ПУ из БС, которые надо удалить"""
    result = []
    meter_eui = set([line.eui for line in result_in.meter_wl.meter_wl])
    list_meter_del = None
    if task_rb.type_task == 'del_list_meter':
        list_meter_del = set(task_rb.param_data[:-1].split(','))
        if len(list_meter_del) > 0:
            meter_eui = meter_eui & list_meter_del
        else:
            return []
    # if task_rb.type_task == 'del_all_meter':
    #     list_meter_del = ''
    if task_rb.meter_true is not None:
        list_meters_true = set(task_rb.meter_true[:-1].split(',')) - meter_eui
        dif_eui = meter_eui - list_meters_true
        dif_eui = list(dif_eui)
        for line_wl in result_in.meter_wl.meter_wl:
            for line_de in dif_eui:
                if line_wl.eui == line_de:
                    result.append(line_wl.id_wl)
                    break
    else:
        result = [line_wlr.id_wl for line_wlr in result_in.meter_wl.meter_wl if line_wlr.eui in meter_eui]
    return result


async def handler_delete_meter(
    con: BaseRequest, token: str, id_for_del: list, task_rb: TaskEquipmentHandlerModelGet, meter_wl: list[MeterWlModel]
) -> MeterWlDelAllModel:
    temp_result = []
    for line in id_for_del:
        for meter in meter_wl:
            if meter.id_wl == line:
                break
        temp_result.append(await get_delete_meter(con, token, line, meter.eui))
    result = MeterWlDelAllModel(empty_wl=False, list_meter_del=task_rb.param_data, meter_wl=temp_result)
    return result


async def get_delete_meter(con: BaseRequest, token: str, id_meter: str, eui_in: str) -> MeterWlDelModel | None:
    """Функция делает запрос для формирования задачи на вычитку парамера по id ПУ"""
    result = None
    api_str = f'devices/{id_meter}'
    shedule_task = await con.delete_request(api_str, token)
    try:
        if shedule_task.status is True:
            shedule_task.data = json.loads(shedule_task.data)
            if 'deleted' in shedule_task.data and shedule_task.data['deleted'] is True:
                result = MeterWlDelModel(id_wl=id_meter, status=True, eui=eui_in)
            else:
                result = MeterWlDelModel(
                    id_wl=id_meter, status=False, error='not valid response', output=str(shedule_task.data), eui=eui_in
                )
        else:
            result = MeterWlDelModel(id_wl=id_meter, status=False, error=str(shedule_task.error), eui=eui_in)
    except Exception as ex:
        result = MeterWlDelModel(id_wl=id_meter, status=False, error=str(ex.args), eui=eui_in)
    return result


async def check_all_del_meter(con: BaseRequest, token: str, task_rb: TaskEquipmentHandlerModelGet) -> bool:
    """Функция выполняетая после удаления ПУ из БС.
    Заправшивает БС с УСПД и проверяет наличие ПУ из списка на удаление"""
    for _ in range(1, 3, 1):
        wl = await get_wl(con, token)
        if wl is not None and wl.status is True:
            break

    if wl.status is True:
        meter_wl = set([meter.eui for meter in wl.meter_wl])
        if task_rb.type_task == 'del_list_meter':
            list_meter_del = set(task_rb.param_data.split(','))
            compare_meter = meter_wl & list_meter_del
            return 'true' if len(compare_meter) == 0 else 'false'
        if task_rb.type_task == 'del_all_meter':
            return 'true' if len(meter_wl) == 0 else 'false'
    else:
        return 'false'
