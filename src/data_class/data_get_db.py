from pydantic import BaseModel, ConfigDict


class TaskFromDbkModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: int
    meter_id: int
    status_task: int


class GetDbTaskModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    host: str
    task: list[TaskFromDbkModel] | None = None
    status: bool
    error: str | None = None
