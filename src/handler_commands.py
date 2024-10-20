from asyncio import sleep
from datetime import datetime

from config import (
    count_repeat_conf,
    list_comannds_get_wl,
    list_comannds_repeat,
    list_command,
    list_command_after_set,
    list_command_del,
)
from handlers.handler_del_meter import hand_result_del
from handlers.handler_get_command import hand_result
from handlers.handler_get_wl import hand_result_get_wl
from logics.del_meter import set_del_meter_wl
from logics.get_command import get_command
from logics.get_wl import get_meter_wl
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
            count_repeat += 1
            await sleep(60)

        if task_rb.type_task in list_command_after_set:
            for _ in range(1, 2, 1):
                await get_after_set(task_rb)

    if task_rb.type_task in list_command_del:
        result_del = await set_del_meter_wl(task_rb)
        await hand_result_del(result_del)

    if task_rb.type_task in list_comannds_get_wl:
        result_del = await get_meter_wl(task_rb)
        await hand_result_get_wl(result_del)

    print(
        f'{datetime.now()}: stop run_command for task {task_rb.task_id}, equipment {task_rb.serial_in_sourse}, command: {task_rb.type_task}'
    )
