from config import timeout_task
from db_handler import get_task_filter_sub_task, set_task
from sql.model import SubTaskModelSet, TaskEquipmentHandlerModelGet, TaskSubTaskModelGet


async def get_after_set(task_rb: TaskEquipmentHandlerModelGet):
    await set_subtask(task_rb)
    sub_task = await get_subtask(task_rb.task_id, task_rb.type_task)
    if sub_task is not None and sub_task.status_task != 'start':
        pass
    print(1)


async def get_subtask(task_id: int, command: str) -> TaskSubTaskModelGet | None:
    task = await get_task_filter_sub_task(task_id)
    if len(task) > 0:
        sub_command = f'get_{command}'
        for line in task:
            if line.type_task == sub_command:
                return line
    return None


async def set_subtask(task_rb: TaskEquipmentHandlerModelGet) -> int | None:
    sub_command = f'get_{task_rb.type_task}'
    sub_task = SubTaskModelSet(
        sub_task_task_id=task_rb.task_id,
        equipment_id=task_rb.equipment_id,
        type_task=sub_command,
        status_task='start',
        timeouut_task=timeout_task[sub_command],
        group_task_id=task_rb.group_task_id,
        param_data=task_rb.param_data,
    )
    await set_task([sub_task])
    print(1)
