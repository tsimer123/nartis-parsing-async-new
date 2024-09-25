from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from sql.engine import async_engine


async def create_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class Base(DeclarativeBase):
    pass


class Equipment(Base):
    # УСПД
    __tablename__ = 'equipment'

    equipment_id: Mapped[int] = mapped_column(primary_key=True)
    serial: Mapped[str | None] = mapped_column(Text)
    serial_in_sourse: Mapped[str] = mapped_column(Text)
    ip1: Mapped[str] = mapped_column(Text)
    ip2: Mapped[str | None] = mapped_column(Text)
    login: Mapped[str] = mapped_column(Text)
    passw: Mapped[str] = mapped_column(Text)
    fw_version: Mapped[str | None] = mapped_column(Text)
    type_equipment: Mapped[str | None] = mapped_column(Text)
    modification: Mapped[str | None] = mapped_column(Text)
    date_response: Mapped[datetime | None] = mapped_column(DateTime)
    created_on: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    update_on: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    meter: Mapped[list['Meter']] = relationship(back_populates='equipment')
    log_equipment: Mapped[list['LogEquipment']] = relationship(back_populates='equipment')
    task: Mapped[list['Task']] = relationship(back_populates='equipment')


class Meter(Base):
    # ПУ
    __tablename__ = 'meter'

    meter_id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int] = mapped_column(Integer, ForeignKey('equipment.equipment_id'))
    id_wl: Mapped[int] = mapped_column(Integer)
    eui: Mapped[str] = mapped_column(Text)
    archive: Mapped[bool] = mapped_column(Boolean)
    included_in_survey: Mapped[bool] = mapped_column(Boolean)
    # state_in_wl: Mapped[str] = mapped_column(Text)
    schedule: Mapped[str | None] = mapped_column(Text)
    schedule_status: Mapped[str | None] = mapped_column(Text)
    schedule_date: Mapped[datetime | None] = mapped_column(DateTime)
    set_schedule_status: Mapped[str | None] = mapped_column(Text)
    set_schedule_date: Mapped[datetime | None] = mapped_column(DateTime)
    leave_time: Mapped[int | None] = mapped_column(Text)
    leave_time_status: Mapped[str | None] = mapped_column(Text)
    leave_time_date: Mapped[datetime | None] = mapped_column(DateTime)
    tariff_mask: Mapped[int | None] = mapped_column(Text)
    tariff_mask_status: Mapped[str | None] = mapped_column(Text)
    tariff_mask_date: Mapped[datetime | None] = mapped_column(DateTime)
    set_tariff_mask_status: Mapped[str | None] = mapped_column(Text)
    set_tariff_mask_date: Mapped[datetime | None] = mapped_column(DateTime)
    fw_meter: Mapped[int | None] = mapped_column(Text)
    fw_meter_status: Mapped[str | None] = mapped_column(Text)
    fw_meter_date: Mapped[datetime | None] = mapped_column(DateTime)
    board_ver: Mapped[int | None] = mapped_column(Text)
    board_ver_status: Mapped[str | None] = mapped_column(Text)
    board_ver_date: Mapped[datetime | None] = mapped_column(DateTime)
    created_on: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    update_on: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    equipment: Mapped['Equipment'] = relationship(back_populates='meter')


class LogEquipment(Base):
    # Лог запросов к УСПД
    __tablename__ = 'log_equipment'

    log_equipment_id: Mapped[int] = mapped_column(primary_key=True)
    # group_task_id: Mapped[int] = mapped_column(Integer, ForeignKey('group_task.group_task_id'))
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey('task.task_id'))
    equipment_id: Mapped[int] = mapped_column(Integer, ForeignKey('equipment.equipment_id'))
    status_response: Mapped[str] = mapped_column(Text)
    # error: Mapped[str | None] = mapped_column(Text)
    response: Mapped[str | None] = mapped_column(Text)
    created_on: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    task: Mapped['Task'] = relationship(back_populates='log_equipment')
    # group_task: Mapped['GroupTask'] = relationship(back_populates='log_equipment')
    equipment: Mapped['Equipment'] = relationship(back_populates='log_equipment')


class Task(Base):
    # Лог запросов к УСПД
    __tablename__ = 'task'

    task_id: Mapped[int] = mapped_column(primary_key=True)
    sub_task_task_id: Mapped[int | None] = mapped_column(Integer)
    group_task_id: Mapped[int] = mapped_column(Integer, ForeignKey('group_task.group_task_id'))
    equipment_id: Mapped[int] = mapped_column(Integer, ForeignKey('equipment.equipment_id'))
    type_task: Mapped[str] = mapped_column(Text)
    param_data: Mapped[str | None] = mapped_column(Text)
    status_task: Mapped[str] = mapped_column(Text)
    meter_true: Mapped[str | None] = mapped_column(Text)
    timeouut_task: Mapped[int] = mapped_column(Integer)
    total_time: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
    created_on: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    update_on: Mapped[datetime | None] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    equipment: Mapped['Equipment'] = relationship(back_populates='task')
    group_task: Mapped['GroupTask'] = relationship(back_populates='task')
    log_equipment: Mapped[list['LogEquipment']] = relationship(back_populates='task')


class GroupTask(Base):
    # Лог запросов к УСПД
    __tablename__ = 'group_task'

    group_task_id: Mapped[int] = mapped_column(primary_key=True)
    created_on: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    task: Mapped[list['Task']] = relationship(back_populates='group_task')
    # log_equipment: Mapped[list['LogEquipment']] = relationship(back_populates='group_task')
