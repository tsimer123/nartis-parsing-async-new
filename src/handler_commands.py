from datetime import datetime

from config import list_command
from handlers.handler_get_command import hand_result
from logics.get_command import get_command
from sql.model import TaskEquipmentHandlerModelGet


async def run_command(task_rb: TaskEquipmentHandlerModelGet):
    result = {'status': False}
    print(
        f'{datetime.now()}: start run_command for task {task_rb.task_id}, equipment {task_rb.serial_in_sourse}, command: {task_rb.type_task}'
    )

    if task_rb.type_task in list_command:
        result = await get_command(task_rb)
        await hand_result(result)
        print(
            f'{datetime.now()}: stop run_command for task {task_rb.task_id}, equipment {task_rb.serial_in_sourse}, command: {task_rb.type_task}'
        )
