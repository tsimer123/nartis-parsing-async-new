from asyncio import sleep
from datetime import datetime

from config import count_repeat_conf, list_comannds_repeat, list_command, list_command_after_set, list_command_del
from data_class.data_get_command import GetComandModel
from handlers.handler_del_meter import hand_result_del
from handlers.handler_get_command import hand_result
from logics.del_meter import set_del_meter_wl
from logics.get_command import get_command
from logics.set_command import get_after_set
from sql.model import TaskEquipmentHandlerModelGet


async def run_command(task_rb: TaskEquipmentHandlerModelGet):
    result = {'status': False}
    print(
        f'{datetime.now()}: start run_command for task {task_rb.task_id}, equipment {task_rb.serial_in_sourse}, command: {task_rb.type_task}'
    )

    if task_rb.type_task in list_command:
        """сверяем тип команды на необходимость повторений (например установка планировщика), в противном случае будет
        одно повторение"""
        repeat = count_repeat_conf if task_rb.type_task in list_comannds_repeat else 2
        count_repeat = 1
        # meter_true = ''
        while count_repeat < repeat:
            result = await get_command(task_rb)
            await hand_result(result)
            if repeat > 1:
                print(
                    f'{datetime.now()}: stop iter: {count_repeat} set run_command for task {task_rb.task_id}, equipment {task_rb.serial_in_sourse}, command: {task_rb.type_task}'
                )

                # meter_true = get_str_eui_hand(result, meter_true)
            count_repeat += 1
            await sleep(60)
        # if repeat > 1:
        #     meter_true = list(set(meter_true.strip(',').split(',')))
        #     await update_true_meter(task_rb, meter_true)
        if task_rb.type_task in list_command_after_set:
            for _ in range(1, 2, 1):
                await get_after_set(task_rb)

    if task_rb.type_task in list_command_del:
        result_del = await set_del_meter_wl(task_rb)
        await hand_result_del(result_del)

    print(
        f'{datetime.now()}: stop run_command for task {task_rb.task_id}, equipment {task_rb.serial_in_sourse}, command: {task_rb.type_task}'
    )


def get_str_eui_hand(result_in: GetComandModel, meter: str) -> str:
    """функция добавляет новые meter_true к уже существующим meter_true с проверкой начилия ПУ в БС"""
    for line in result_in.meter_wl.meter_wl:
        if line.task_hand_log is not None and line.task_hand_log.status_task_db == 'true':
            meter = meter + line.eui + ','
    return meter
