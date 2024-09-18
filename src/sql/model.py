from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EquipmentModelSet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    serial: str | None = None
    serial_in_sourse: str
    login: str = 'admin'
    passw: str = 'admin'
    ip1: str
    ip2: str | None = None
    fw_version: str | None = None
    type_equipment: str | None = None
    modification: str | None = None
    date_response: datetime | None = None


class EquipmentModelGet(EquipmentModelSet):
    model_config = ConfigDict(from_attributes=True)

    equipment_id: int
    created_on: datetime
    update_on: datetime


class TaskModelSet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    group_task_id: int
    equipment_id: int
    type_task: str
    status_task: str  # true/false/start
    meter_true: str | None = None
    timeouut_task: int
    param_data: str | None = None


class TaskModelGet(TaskModelSet):
    task_id: int
    created_on: datetime
    update_on: datetime


class TaskEquipmentModelGet(TaskModelGet):
    serial_in_sourse: str


class TaskEquipmentHandlerModelGet(TaskEquipmentModelGet):
    ip1: str
    ip2: str | None
    login: str
    passw: str
    time_zone: int
    param_data: str | None = None


class TaskModelUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: int
    group_task_id: int
    type_task: str | None = None
    status_task: str | None = None
    meter_true: str | None = None
    # total_time: int | None = None
    # timeouut_task: int
    created_on: datetime | None = None
    update_on: datetime | None = None


class TaskHandModelUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: int
    status_task: str | None = None
    meter_true: str | None = None
    # timeouut_task: int | None = None
    error: str | None = None
    total_time: int | None = None


class TaskMeterTrueModelUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: int
    meter_true: str


class EquipmentHandModelUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    equipment_id: int
    serial: str
    fw_version: str
    type_equipment: str
    modification: str
    date_response: datetime


class MeterHandModelSet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    equipment_id: int
    id_wl: int
    eui: str
    archive: bool
    included_in_survey: bool
    schedule: str | None = None
    schedule_status: str | None = None
    schedule_date: datetime | None = None
    set_schedule_status: str | None = None
    set_schedule_date: datetime | None = None
    leave_time: int | None = None
    leave_time_status: str | None = None
    leave_time_date: datetime | None = None
    tariff_mask: int | None = None
    tariff_mask_status: str | None = None
    tariff_mask_date: datetime | None = None
    set_tariff_mask_status: str | None = None
    set_tariff_mask_date: datetime | None = None
    fw_meter: str | None = None
    fw_meter_status: str | None = None
    fw_meter_date: datetime | None = None
    board_ver: str | None = None
    board_ver_status: str | None = None
    board_ver_date: datetime | None = None


class MeterHandModelGet(MeterHandModelSet):
    model_config = ConfigDict(from_attributes=True)

    meter_id: int


class MeterModelUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    meter_id: int
    id_wl: int | None = None
    archive: bool | None = None
    included_in_survey: bool | None = None
    schedule: str | None = None
    schedule_status: str | None = None
    schedule_date: datetime | None = None
    set_schedule_status: str | None = None
    set_schedule_date: datetime | None = None
    leave_time: int | None = None
    leave_time_status: str | None = None
    leave_time_date: datetime | None = None
    tariff_mask: int | None = None
    tariff_mask_status: str | None = None
    tariff_mask_date: datetime | None = None
    set_tariff_mask_status: str | None = None
    set_tariff_mask_date: datetime | None = None
    fw_meter: str | None = None
    fw_meter_status: str | None = None
    fw_meter_date: datetime | None = None
    board_ver: str | None = None
    board_ver_status: str | None = None
    board_ver_date: datetime | None = None


class LogHandModelSet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: int
    equipment_id: int
    status_response: bool
    response: str | None = None
