import asyncpg

from config import DB_PASS, DB_USER
from data_class.data_get_db import GetDbTaskModel, TaskFromDbkModel


async def get_db_task(ip: str, port: str = '5432') -> GetDbTaskModel:
    uspd = GetDbTaskModel(host=ip, status=False)

    try:
        conn = await asyncpg.connect(user=DB_USER, password=DB_PASS, database='uspd', host=ip, port=port)
        tasks = await conn.fetch('select id, meter_id,  status from tasks order by id desc')
        if len(tasks) > 0:
            uspd.task = []
            for line in tasks:
                temp_dict = dict(line)
                if temp_dict['status'] is None:
                    temp_dict['status'] = 3
                if (
                    temp_dict['status'] is not None
                    and temp_dict['id'] is not None
                    and temp_dict['meter_id'] is not None
                ):
                    uspd.task.append(
                        TaskFromDbkModel(
                            task_id=temp_dict['id'], meter_id=temp_dict['meter_id'], status_task=temp_dict['status']
                        )
                    )
        uspd.status = True
        await conn.close()
    except Exception as ex:
        str_error = f'Host: {ip}:{port}, text ex: {str(ex.args)}'
        print(ex)
        uspd.error = str_error

    return uspd
