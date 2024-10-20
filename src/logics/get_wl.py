from datetime import datetime

from aiohttp import ClientSession, CookieJar

from base_http.base import BaseRequest
from data_class.data_get_command import GetComandModel
from logics.general_func import get_dev_info, get_tzcode, get_wl_for_wl
from sql.model import (
    TaskEquipmentHandlerModelGet,
)


async def get_meter_wl(task_rb: TaskEquipmentHandlerModelGet):
    start_time = datetime.now()
    print(
        f'{datetime.now()}: start get_meter_wl for task {task_rb.task_id}, equipment {task_rb.serial_in_sourse}, command: {task_rb.type_task}'
    )
    result = GetComandModel(
        task_id=task_rb.task_id,
        equipment_id=task_rb.equipment_id,
        type_task=task_rb.type_task,
        status_task='false',
        meter_true=task_rb.meter_true,
        time_zone=task_rb.time_zone,
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
                    result.time_zone = timezone
                # получаем данные по УСПД
                result.equipment_info = await get_dev_info(con, token)
                # получаем БС из УСПД
                result.meter_wl_wl = await get_wl_for_wl(con, token)
                if result.meter_wl_wl is not None:
                    if result.meter_wl_wl.status is True:
                        result.status_task = 'true'
                    else:
                        result.error = str(result.meter_wl_wl.error)
                else:
                    result.error = 'Не предвиденная ошибка: meter_wl = None'
            except Exception as ex:
                result.error = str(ex.args)
        else:
            print('????')
            result.error = str(auth.error)
    end_time = datetime.now()
    delta = end_time - start_time
    result.total_time = round(delta.total_seconds())
    print(
        f'{datetime.now()}: stop get data for task {task_rb.task_id}, equipment {task_rb.serial_in_sourse}, command: {task_rb.type_task}, total time {result.total_time}'
    )

    return result
