from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MeterWlForWlModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_wl_in_uspd: int
    eui: str
    archive: bool
    included_in_survey: bool
    added: datetime
    id_interface: int
    id_model: int
    last_success_time: datetime | None = None
    name: str | None = None
    mod_name: str | None = None
    serial: str | None = None
    res_name: str | None = None


class MeterWlForWLAllModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: bool
    error: str | None = None
    meter_wl: list[MeterWlForWlModel] | None = None
