from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskGetModel(BaseModel):
    """Сохраняем результат http запроса"""

    model_config = ConfigDict(from_attributes=True)

    status: bool
    error: str | None = None
    task_id: int | None = None


class ListTaskModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: int
    meter_id: int | None = None
    status_task_db: str = 'wait'  # true/false/wait
    response: dict | None = None
    status_hand: bool = False
    error: str | None = None


# class TaskHandModel(BaseModel):
#     """Сохраняем результат обработки таски"""

#     model_config = ConfigDict(from_attributes=True)

#     status: bool
#     error: str | None = None
#     task_id: str | None = None


class MeterWlModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_wl: int
    eui: str
    archive: bool
    included_in_survey: bool
    schedule: str | None = None
    schedule_status: str | None = None
    schedule_date: datetime | None = None
    set_schedule_status: str | None = None
    set_schedule_date: datetime | None = None
    leave_time: str | None = None
    leave_time_status: str | None = None
    leave_time_date: datetime | None = None
    tariff_mask: str | None = None
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
    task_log: TaskGetModel | None = None
    task_hand_log: ListTaskModel | None = None


class MeterWlDelModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_wl: int
    status: bool
    eui: str | None = None
    output: str | None = None
    error: str | None = None


class MeterWlAllModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: bool
    error: str | None = None
    meter_wl: list[MeterWlModel] | None = None


class MeterWlDelAllModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    empty_wl: bool
    list_meter_del: str
    error: str | None = None
    meter_wl: list[MeterWlDelModel] | None = None


class EquipmentInfoModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: bool
    error: str | None = None
    serial: str | None = None
    fw_version: str | None = None
    type_equipment: str | None = None
    modification: str | None = None
    date_response: datetime


class GetComandModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: int
    equipment_id: int
    type_task: str
    status_task: str
    meter_true: str | None
    meter_wl: MeterWlAllModel | None = None
    meter_wl_del: MeterWlDelAllModel | None = None
    equipment_info: EquipmentInfoModel | None = None
    error: str | None = None
    total_time: int | None = None
    error_status_hand_task: str | None = None


class GetResultTaskModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: bool
    error: str | None = None
    data: dict | None = None


class StatusHandModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: bool = False
    list_task: list[ListTaskModel]
    error: str | None = None
