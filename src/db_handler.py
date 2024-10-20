import os
from datetime import datetime

from sqlalchemy import and_, delete, insert, select, update

from config import db_name
from sql.engine import get_async_session
from sql.model import (
    EquipmentHandModelUpdate,
    EquipmentModelGet,
    EquipmentModelSet,
    LogHandModelSet,
    MeterDelHandModelDel,
    MeterDelHandModelGet,
    MeterDelHandModelSet,
    MeterDelHandModelUpdate,
    MeterHandModelGet,
    MeterHandModelSet,
    MeterModelUpdate,
    MeterNewModelGet,
    MeterNewModelSet,
    MeterWLModelGet,
    MeterWLModelSet,
    MeterWLModelUpdate,
    SubTaskModelSet,
    TaskEquipmentHandlerModelGet,
    TaskEquipmentModelGet,
    TaskHandModelUpdate,
    TaskMeterTrueModelUpdate,
    TaskModelGet,
    TaskModelSet,
    TaskModelUpdate,
    TaskSubTaskModelGet,
)
from sql.scheme import Equipment, GroupTask, LogEquipment, Meter, MeterDel, MeterNew, Task, Wl, create_db


async def start_db(type_start):
    if type_start == 'clear':
        try:
            os.remove(db_name)
        except FileNotFoundError as ex:
            print(ex.args)

    await create_db()


async def set_grouptask() -> int:
    stmt = insert(GroupTask).returning(GroupTask.group_task_id)

    session = [session async for session in get_async_session()][0]

    result = await session.execute(stmt)
    await session.commit()

    group_task_id = None
    for line in result.scalars():
        group_task_id = line
        break

    await session.close()

    return group_task_id


async def get_equipment_filter(in_equipments: list[str]) -> list[EquipmentModelGet]:
    """получение всех УСПД из БД по номерам из файла host.xlsx"""
    stmt = select(Equipment).where(Equipment.serial_in_sourse.in_(in_equipments))

    session = [session async for session in get_async_session()][0]

    result = await session.execute(stmt)

    uspd_get = []

    for a in result.scalars():
        uspd_get.append(init_get_uspd(a))

    await session.close()

    return uspd_get


async def set_equipment(equipment: list[EquipmentModelSet]) -> None:
    # a = [line_eq.model_dump(exclude_none=True) for line_eq in equipment]
    stmt = insert(Equipment).values([line_eq.model_dump() for line_eq in equipment])

    session = [session async for session in get_async_session()][0]

    await session.execute(stmt)
    await session.commit()
    await session.close()
    # print(1)


async def set_task(task: list[TaskModelSet]) -> None:
    session = [session async for session in get_async_session()][0]
    try:
        stmt = insert(Task).values([line_t.model_dump(exclude_unset=True) for line_t in task])

        await session.execute(stmt)
        await session.commit()
        await session.close()
    except Exception as ex:
        print(ex.args)
    await session.close()


async def get_task_equipment_filter(equipment_id: list[int]) -> list[TaskEquipmentModelGet]:
    """получение всех task из БД по equipment_id"""
    stmt = select(Task, Equipment).join(Task.equipment).where(Task.equipment_id.in_(equipment_id))
    # stmt = select(Task).where(Task.equipment_id.in_(equipment_id))

    session = [session async for session in get_async_session()][0]

    result = await session.execute(stmt)

    uspd_get = []

    for line in result.scalars():
        uspd_get.append(init_get_task_equipment(line))

    await session.close()

    return uspd_get


async def update_task(task: list[TaskModelUpdate]) -> None:
    data_update = [line_t.model_dump(exclude_none=True) for line_t in task]

    session = [session async for session in get_async_session()][0]

    stmt = update(Task)
    # print(stmt)
    await session.execute(stmt, data_update)
    await session.commit()
    await session.close()


async def get_task_grouptask(group_task_id: int, time_zone: int) -> list[TaskEquipmentHandlerModelGet]:
    """получение всех task из БД по equipment_id"""
    stmt = select(Task, Equipment).join(Task.equipment).where(Task.group_task_id.in_([group_task_id]))

    session = [session async for session in get_async_session()][0]

    result = await session.execute(stmt)

    task_get = []

    for line in result.scalars():
        task_get.append(await init_get_task_equipment_for_handler(line, time_zone))
    await session.close()

    return task_get


async def get_meter_filter(in_meter: list[str]) -> list[MeterHandModelGet]:
    """получение всех ПУ из БД по EUI"""
    stmt = select(Meter).where(Meter.eui.in_(in_meter))

    session = [session async for session in get_async_session()][0]

    result = await session.execute(stmt)

    uspd_get = []

    for a in result.scalars():
        uspd_get.append(init_get_meter(a))

    await session.close()

    return uspd_get


async def get_meter_new_filter(in_meter: list[str]) -> list[MeterNewModelGet]:
    """получение всех ПУ из БД по EUI"""
    stmt = select(MeterNew).where(MeterNew.eui.in_(in_meter))

    session = [session async for session in get_async_session()][0]

    result = await session.execute(stmt)

    uspd_get = []

    for a in result.scalars():
        uspd_get.append(init_get_meter_new(a))

    await session.close()

    return uspd_get


async def set_meter_new(meter_new: list[MeterNewModelSet]) -> None | list:
    stmt = insert(MeterNew).values([line_mn.model_dump() for line_mn in meter_new])

    try:
        session = [session async for session in get_async_session()][0]

        await session.execute(stmt)

        await session.commit()
        result = None

    except Exception as ex:
        await session.rollback()
        print(f'{datetime.now()}: ---------- Ошибка записи в БД сервиса: {ex.args}')
        result = ex.args
    await session.close()
    return result


async def update_data_after_hand(
    task: TaskHandModelUpdate,
    equipment: EquipmentHandModelUpdate | None,
    meter: dict[list[MeterHandModelSet], list[MeterModelUpdate]],
    log: LogHandModelSet,
) -> None:
    """Занесение результатов по одной таске get_command"""
    session = [session async for session in get_async_session()][0]
    try:
        task_update = [task.model_dump()]
        stmt_task = update(Task)
        await session.execute(stmt_task, task_update)

        if equipment is not None:
            equipment_update = [equipment.model_dump()]
            stmt_equipment = update(Equipment)
            await session.execute(stmt_equipment, equipment_update)

        if len(meter['update_meter']) > 0:
            meter_update = [line_um.model_dump(exclude_none=True) for line_um in meter['update_meter']]
            stmt_meter_update = update(Meter)
            await session.execute(stmt_meter_update, meter_update)

        if len(meter['create_meter']) > 0:
            value = [line_cm.model_dump() for line_cm in meter['create_meter']]
            meter_create = insert(Meter).values(value)
            # print('111111111111')
            # print(meter_create)
            await session.execute(meter_create)

        stmt_log = insert(LogEquipment).values([log.model_dump()])
        await session.execute(stmt_log)

        await session.commit()
    except Exception as ex:
        await session.rollback()
        print(f'{datetime.now()}: ---------- Ошибка записи в БД сервиса: {ex.args}')
    await session.close()


async def update_task_meter_true(task: TaskMeterTrueModelUpdate) -> None:
    data_update = [task.model_dump()]

    session = [session async for session in get_async_session()][0]

    stmt = update(Task)
    # print(stmt)
    await session.execute(stmt, data_update)
    await session.commit()
    await session.close()


async def get_task_filter_sub_task(sub_task_id: int) -> list[TaskSubTaskModelGet]:
    """получение Тасок из БД по sub_task_id"""
    stmt = select(Task).where(Task.sub_task_task_id == sub_task_id).order_by(Task.task_id)

    session = [session async for session in get_async_session()][0]

    result = await session.execute(stmt)

    task_id = []

    for line in result.scalars():
        task_id.append(await init_get_task_sub_task(line))

    await session.close()

    return task_id


async def get_meter_filter_equipment(equipment_id: int) -> list[MeterHandModelGet]:
    """получение всех ПУ из БД по EUI"""
    stmt = select(Meter).where(Meter.equipment_id == equipment_id)

    session = [session async for session in get_async_session()][0]

    result = await session.execute(stmt)

    uspd_get = []

    for a in result.scalars():
        uspd_get.append(init_get_meter(a))

    await session.close()

    return uspd_get


async def get_wl_filter_equipment(equipment_id: int) -> list[MeterWLModelGet]:
    """получение всех WL из БД по equipment_id"""
    stmt = select(Wl, MeterNew).join(MeterNew.wl).where(Wl.equipment_id == equipment_id)

    session = [session async for session in get_async_session()][0]

    result = await session.execute(stmt)

    uspd_get = []

    for a in result.scalars():
        uspd_get.append(init_get_wl(a))

    await session.close()

    return uspd_get


async def set_one_task_return_id(task: SubTaskModelSet) -> int:
    stmt = insert(Task).values(task.model_dump(exclude_unset=True)).returning(Task.task_id)

    session = [session async for session in get_async_session()][0]

    result = await session.execute(stmt)
    await session.commit()

    group_task_id = None
    for line in result.scalars():
        group_task_id = line
        break

    await session.close()

    return group_task_id


async def get_task_filter_task(task_id: int, time_zone: int) -> list[TaskEquipmentHandlerModelGet]:
    """получение всех task из БД по equipment_id"""
    stmt = select(Task, Equipment).join(Task.equipment).where(Task.task_id == task_id)

    session = [session async for session in get_async_session()][0]

    result = await session.execute(stmt)

    task_get = []

    for line in result.scalars():
        task_get.append(await init_get_task_equipment_for_handler(line, time_zone))
    await session.close()

    return task_get


async def get_meter_del_filter(in_meter: list[str], equipment_id_in: int) -> list[MeterDelHandModelGet]:
    """получение всех удаляемых ПУ из БД по EUI и УСПД"""
    stmt = select(MeterDel).where(and_(MeterDel.eui.in_(in_meter), MeterDel.equipment_id == equipment_id_in))

    session = [session async for session in get_async_session()][0]

    result = await session.execute(stmt)

    uspd_get = []

    for a in result.scalars():
        uspd_get.append(init_get_meter_del(a))

    await session.close()

    return uspd_get


async def update_data_after_hand_delete_meter(
    task: TaskHandModelUpdate,
    equipment: EquipmentHandModelUpdate | None,
    meter: dict[list[MeterDelHandModelUpdate], list[MeterDelHandModelSet], list[MeterDelHandModelDel]],
    log: LogHandModelSet,
) -> None:
    """Занесение результатов по удальению ПУ из БС командами из списка list_command_del"""
    session = [session async for session in get_async_session()][0]
    try:
        task_update = [task.model_dump()]
        stmt_task = update(Task)
        await session.execute(stmt_task, task_update)

        if equipment is not None:
            equipment_update = [equipment.model_dump()]
            stmt_equipment = update(Equipment)
            await session.execute(stmt_equipment, equipment_update)

        if len(meter['update_meter']) > 0:
            meter_update = [line_um.model_dump(exclude_none=True) for line_um in meter['update_meter']]
            stmt_meter_update = update(MeterDel)
            await session.execute(stmt_meter_update, meter_update)

        if len(meter['create_meter']) > 0:
            value = [line_cm.model_dump() for line_cm in meter['create_meter']]
            meter_create = insert(MeterDel).values(value)
            await session.execute(meter_create)

        if len(meter['delete_meter']) > 0:
            meter_delete = [line_um.model_dump(exclude_none=True) for line_um in meter['delete_meter']]
            stmt_meter_update = delete(MeterDel).where(MeterDel.eui.in_(meter_delete))
            await session.execute(stmt_meter_update, meter_update)

        stmt_log = insert(LogEquipment).values([log.model_dump()])
        await session.execute(stmt_log)

        await session.commit()
    except Exception as ex:
        await session.rollback()
        print(f'{datetime.now()}: ---------- Ошибка записи в БД сервиса: {ex.args}')
    await session.close()


async def update_data_after_hand_get_wl(
    task: TaskHandModelUpdate,
    equipment: EquipmentHandModelUpdate | None,
    meter: dict[list[MeterWLModelUpdate], list[MeterWLModelSet]],
    log: LogHandModelSet,
) -> None:
    """Занесение результатов по удальению ПУ из БС командами из списка list_command_del"""
    session = [session async for session in get_async_session()][0]
    try:
        task_update = [task.model_dump()]
        stmt_task = update(Task)
        await session.execute(stmt_task, task_update)

        if equipment is not None:
            equipment_update = [equipment.model_dump()]
            stmt_equipment = update(Equipment)
            await session.execute(stmt_equipment, equipment_update)

        if len(meter['update_wl']) > 0:
            meter_update = [line_um.model_dump(exclude_none=True) for line_um in meter['update_wl']]
            stmt_meter_update = update(Wl)
            await session.execute(stmt_meter_update, meter_update)

        if len(meter['create_wl']) > 0:
            value = [line_cm.model_dump() for line_cm in meter['create_wl']]
            meter_create = insert(Wl).values(value)
            await session.execute(meter_create)

        stmt_log = insert(LogEquipment).values([log.model_dump()])
        await session.execute(stmt_log)

        await session.commit()
        result = None
    except Exception as ex:
        await session.rollback()
        print(f'{datetime.now()}: ---------- Ошибка записи в БД сервиса: {ex.args}')
        result = ex.args
    await session.close()
    return result


def init_get_uspd(uspd: Equipment) -> EquipmentModelGet:
    temp_uspd = EquipmentModelGet(
        equipment_id=uspd.equipment_id,
        serial=uspd.serial,
        serial_in_sourse=uspd.serial_in_sourse,
        ip1=uspd.ip1,
        ip2=uspd.ip2,
        fw_version=uspd.fw_version,
        type_equipment=uspd.type_equipment,
        modification=uspd.modification,
        date_response=uspd.date_response,
        created_on=uspd.created_on,
        update_on=uspd.update_on,
    )
    return temp_uspd


def init_get_task(task: Task) -> TaskModelGet:
    temp_uspd = TaskModelGet(
        task_id=task.task_id,
        equipment_id=task.equipment_id,
        type_task=task.type_task,
        status_task=task.status_task,
        meter_true=task.meter_true,
        timeouut_task=task.timeouut_task,
        created_on=task.created_on,
        update_on=task.update_on,
    )
    return temp_uspd


def init_get_task_equipment(task: Task) -> TaskEquipmentModelGet:
    temp_uspd = TaskEquipmentModelGet(
        task_id=task.task_id,
        group_task_id=task.group_task_id,
        equipment_id=task.equipment_id,
        type_task=task.type_task,
        status_task=task.status_task,
        meter_true=task.meter_true,
        timeouut_task=task.timeouut_task,
        created_on=task.created_on,
        update_on=task.update_on,
        serial_in_sourse=task.equipment.serial_in_sourse,
    )
    return temp_uspd


async def init_get_task_equipment_for_handler(task: Task, time_zone: int) -> TaskEquipmentHandlerModelGet:
    temp_uspd = TaskEquipmentHandlerModelGet(
        group_task_id=task.group_task_id,
        task_id=task.task_id,
        equipment_id=task.equipment_id,
        type_task=task.type_task,
        status_task=task.status_task,
        meter_true=task.meter_true,
        timeouut_task=task.timeouut_task,
        created_on=task.created_on,
        update_on=task.update_on,
        serial_in_sourse=task.equipment.serial_in_sourse,
        ip1=task.equipment.ip1,
        ip2=task.equipment.ip2,
        login=task.equipment.login,
        passw=task.equipment.passw,
        time_zone=time_zone,
        param_data=task.param_data,
    )
    return temp_uspd


def init_get_meter(meter: Meter) -> MeterHandModelGet:
    temp_meter = MeterHandModelGet(
        meter_id=meter.meter_id,
        equipment_id=meter.equipment_id,
        id_wl=meter.id_wl,
        eui=meter.eui,
        archive=meter.archive,
        included_in_survey=meter.included_in_survey,
        schedule=meter.schedule,
        schedule_status=meter.schedule_status,
        schedule_date=meter.schedule_date,
        set_schedule_status=meter.set_schedule_status,
        set_schedule_date=meter.set_schedule_date,
        leave_time=meter.leave_time,
        leave_time_status=meter.leave_time_status,
        leave_time_date=meter.leave_time_date,
        tariff_mask=meter.tariff_mask,
        tariff_mask_status=meter.tariff_mask_status,
        tariff_mask_date=meter.tariff_mask_date,
        set_tariff_mask_status=meter.set_tariff_mask_status,
        set_tariff_mask_date=meter.set_tariff_mask_date,
        fw_meter=meter.fw_meter,
        fw_meter_status=meter.fw_meter_status,
        fw_meter_date=meter.fw_meter_date,
        board_ver=meter.board_ver,
        board_ver_status=meter.board_ver_status,
        board_ver_date=meter.board_ver_date,
    )
    return temp_meter


def init_get_meter_new(meter: MeterNew) -> MeterNewModelGet:
    temp_meter = MeterNewModelGet(
        meter_new_id=meter.meter_new_id,
        eui=meter.eui,
    )
    return temp_meter


def init_get_wl(wl: Wl) -> MeterWLModelGet:
    temp_meter = MeterWLModelGet(
        wl_id=wl.wl_id,
        eui=wl.meter_new.eui,
        equipment_id=wl.equipment_id,
        meter_new_id=wl.meter_new_id,
        id_wl_in_uspd=wl.id_wl_in_uspd,
        present=wl.present,
        archive=wl.archive,
        included_in_survey=wl.included_in_survey,
        added=wl.added,
        id_interface=wl.id_interface,
        id_model=wl.id_model,
        last_success_time=wl.last_success_time,
        name=wl.name,
        mod_name=wl.mod_name,
        serial=wl.serial,
        res_name=wl.res_name,
    )
    return temp_meter


async def init_get_task_sub_task(task: Task) -> TaskSubTaskModelGet:
    temp_uspd = TaskSubTaskModelGet(
        task_id=task.task_id,
        group_task_id=task.group_task_id,
        sub_task_task_id=task.sub_task_task_id,
        equipment_id=task.equipment_id,
        type_task=task.type_task,
        status_task=task.status_task,
        meter_true=task.meter_true,
        timeouut_task=task.timeouut_task,
        param_data=task.param_data,
        total_time=task.total_time,
        created_on=task.created_on,
        update_on=task.update_on,
    )
    return temp_uspd


def init_get_meter_del(meter_del: MeterDel) -> MeterDelHandModelGet:
    temp_meter = MeterDelHandModelGet(
        meter_del_id=meter_del.meter_del_id,
        equipment_id=meter_del.equipment_id,
        id_wl=meter_del.id_wl,
        eui=meter_del.eui,
        delete_status=meter_del.delete_status,
    )
    return temp_meter
