from asyncio import sleep
from datetime import datetime, timedelta

from config import timeout_task
from db_handler import (
    get_meter_filter_equipment,
    get_task_filter_sub_task,
    get_task_filter_task,
    set_one_task_return_id,
    update_task,
)
from handlers.handler_get_command import hand_result
from logics.get_command import get_command
from sql.model import (
    MeterHandModelGet,
    SubTaskModelSet,
    TaskEquipmentHandlerModelGet,
    TaskModelUpdate,
    TaskSubTaskModelGet,
)


async def get_after_set(task_rb: TaskEquipmentHandlerModelGet):
    print(
        f'{datetime.now()}: start get_after_set for task {task_rb.task_id}, equipment {task_rb.serial_in_sourse}, command: {task_rb.type_task}'
    )
    sub_task = await get_subtask(task_rb.task_id, task_rb.type_task)
    # проверям наличие суб таски в БД
    if sub_task is not None:
        sub_task_id = None
        for _ in range(1, 3, 1):
            # проверям статус стуб таски в БД
            if sub_task.status_task != 'start' or (
                sub_task.status_task == 'start'
                and (datetime.now() > sub_task.update_on + timedelta(seconds=sub_task.timeouut_task))
            ):
                # суб таска уже отработана или просрочена, получаем ПУ по ней
                meter_task = await get_meter_filter_equipment(task_rb.equipment_id)
                if len(meter_task) > 0:
                    """если ПУ есть, то проверяем отработаны ли ПУ по таске, если есть ПУ с полученными данными после 
                    создания set параметра, то заносим их в true_meter get_set субтаске"""
                    meter_true_subtask = get_meter_true_subtask(task_rb, meter_task)
                    # обновляем в get_set субтаске true_meter
                    sub_task_update = TaskModelUpdate(task_id=sub_task.task_id, meter_true=meter_true_subtask)
                    await update_task([sub_task_update])
                    sub_task_id = sub_task.task_id
                break

            # если таска старт то попробуем подождать
            if sub_task.status_task == 'start' and (
                datetime.now() < sub_task.update_on + timedelta(seconds=sub_task.timeouut_task)
            ):
                await sleep(30)

    else:
        sub_task_id = await set_subtask(task_rb)

    if sub_task_id is not None:
        # если есть суб таска то запускаем get
        sub_task_for_get = await get_task_filter_task(sub_task_id, task_rb.time_zone)
        result = await get_command(sub_task_for_get[0])
        await hand_result(result)

        """проверяем полученные данные по таске и вилидируем их, если параметры применились не полностью 
        обновим true_meter в таске set"""
        meter_task = await get_meter_filter_equipment(task_rb.equipment_id)
        if len(meter_task) > 0:
            meter_true_task = get_meter_true_task(task_rb, meter_task)
            task_update = TaskModelUpdate(task_id=sub_task_id, meter_true=meter_true_task)
            await update_task([task_update])
    else:
        print('нет субтасок для обработки')

    print(
        f'{datetime.now()}: stop get_after_set for task {task_rb.task_id}, equipment {task_rb.serial_in_sourse}, command: {task_rb.type_task}'
    )


async def get_subtask(task_id: int, command: str) -> TaskSubTaskModelGet | None:
    task = await get_task_filter_sub_task(task_id)
    if len(task) > 0:
        sub_command = f'get_{command}'
        for line in task:
            if line.type_task == sub_command:
                return line
    return None


async def set_subtask(task_rb: TaskEquipmentHandlerModelGet, meter_true: str = None) -> int:
    sub_command = f'get_{task_rb.type_task}'
    sub_task = SubTaskModelSet(
        group_task_id=task_rb.group_task_id,
        sub_task_task_id=task_rb.task_id,
        equipment_id=task_rb.equipment_id,
        type_task=sub_command,
        status_task='start',
        meter_true=meter_true,
        timeouut_task=timeout_task[sub_command],
        param_data=task_rb.param_data,
    )
    sub_task_id = await set_one_task_return_id(sub_task)
    return sub_task_id


async def get_meter_task(equipment_id: int) -> list[MeterHandModelGet]:
    return get_meter_filter_equipment(equipment_id)


def get_meter_true_task(task_rb: TaskEquipmentHandlerModelGet, meter: list[MeterHandModelGet]) -> str | None:
    # функция выбирает сборщик meter_true по команде для set_команда
    if task_rb.type_task == 'set_shedule':
        meter_true = get_meter_true_shedull_task(meter, task_rb)

    if task_rb.type_task == 'set_tarif_mask':
        meter_true = get_meter_true_tarif_mask_task(meter, task_rb)

    return meter_true


def get_meter_true_subtask(task_rb: TaskEquipmentHandlerModelGet, meter: list[MeterHandModelGet]) -> str | None:
    # функция выбирает сборщик meter_true по команде для get_set_команда
    if task_rb.type_task == 'set_shedule':
        meter_true = get_meter_true_shedull_subtask(meter)

    if task_rb.type_task == 'set_tarif_mask':
        meter_true = get_meter_true_tarif_mask_subtask(meter)

    return meter_true


def get_meter_true_shedull_subtask(meter: list[MeterHandModelGet]) -> str | None:
    # функция собирает meter_true для таски get_set_shedull, для исключения запроса данных после set
    meter_true = ''
    for line in meter:
        if (
            line.set_schedule_status == 'valid'
            and line.schedule_status == 'valid'
            and line.schedule_date > line.set_schedule_date
        ):
            meter_true = meter_true + line.eui + ','
    if len(meter_true) > 0:
        return meter_true
    else:
        return None


def get_meter_true_shedull_task(meter: list[MeterHandModelGet], task_rb: TaskEquipmentHandlerModelGet) -> str | None:
    # функция собирает meter_true для таски set_shedulle, для последующего перезапроса set запроса
    meter_true = ''
    for line_m in meter:
        if (
            line_m.set_schedule_status == 'valid'
            and line_m.schedule_status == 'valid'
            and line_m.schedule_date > line_m.set_schedule_date
            and line_m.schedule is not None
        ):
            # {'task_0': {'type': 'archive daily', 'day': '01', 'time': '13:53'},
            #  'task_1': {'type': 'quality', 'day': '01', 'time': '02:48'},
            # 'task_2': {'type': 'load profile', 'day': '01', 'time': '01:25'},
            #  'task_3': {'type': 'no', 'day': '01', 'time': '00:00'}}
            temp_dict_shedule: dict = eval(line_m.schedule)
            param_data = task_rb.param_data.split(',')
            trigger_param = 0
            for line_tds in temp_dict_shedule.values():
                if line_tds['type'] in param_data:
                    trigger_param += 1
            if trigger_param == 4:
                meter_true = meter_true + line_m.eui + ','
    if len(meter_true) > 0:
        return meter_true
    else:
        return None


def get_meter_true_tarif_mask_subtask(meter: list[MeterHandModelGet]) -> str | None:
    # функция собирает meter_true для таски get_set_tarif_mask, для исключения запроса данных после set
    meter_true = ''
    for line in meter:
        if (
            line.set_tariff_mask_status == 'valid'
            and line.tariff_mask_status == 'valid'
            and line.tariff_mask_date > line.set_tariff_mask_date
        ):
            meter_true = meter_true + line.eui + ','
    if len(meter_true):
        return meter_true
    else:
        return None


def get_meter_true_tarif_mask_task(meter: list[MeterHandModelGet], task_rb: TaskEquipmentHandlerModelGet) -> str | None:
    # функция собирает meter_true для таски set_tarif_mask, для последующего перезапроса set запроса
    meter_true = ''
    for line in meter:
        if (
            line.set_tariff_mask_status == 'valid'
            and line.tariff_mask_status == 'valid'
            and line.tariff_mask_date > line.set_tariff_mask_date
            and line.tariff_mask is not None
            and line.tariff_mask == int(task_rb.param_data)
        ):
            meter_true = meter_true + line.eui + ','
    if len(meter_true):
        return meter_true
    else:
        return None
