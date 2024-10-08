from pydantic import BaseModel, ConfigDict
from pydantic.networks import IPvAnyAddress


class UspdEquipmentInExcel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    ip1: IPvAnyAddress
    ip2: IPvAnyAddress | None = None
    login: str = 'admin'
    passw: str = 'admin'


class EquipmentInExcel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sub_task_id: int | None = None
    uspd: UspdEquipmentInExcel
    command: str
    meters: list = []
    param_data: str | None = None
