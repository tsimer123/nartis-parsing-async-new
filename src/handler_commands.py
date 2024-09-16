from datetime import datetime

from handlers.handler_get_command import hand_result
from logics.get_command import get_command
from sql.model import TaskEquipmentHandlerModelGet


async def run_command(task_rb: TaskEquipmentHandlerModelGet):
    result = {'status': False}
    print(
        f'{datetime.now()}: start run_command for task {task_rb.task_id}, equipment {task_rb.serial_in_sourse}, command: {task_rb.type_task}'
    )

    if (
        task_rb.type_task == 'get_shedule'
        or task_rb.type_task == 'get_leave_time'
        or task_rb.type_task == 'get_tarif_mask'
        or task_rb.type_task == 'set_leave_time'
        or task_rb.type_task == 'set_tarif_mask'
    ):
        result = await get_command(task_rb)
        await hand_result(result)
        print(
            f'{datetime.now()}: stop run_command for task {task_rb.task_id}, equipment {task_rb.serial_in_sourse}, command: {task_rb.type_task}'
        )
