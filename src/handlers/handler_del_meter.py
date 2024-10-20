from datetime import datetime

from config import timeout_task
from data_class.data_get_command import GetComandModel
from db_handler import get_meter_del_filter, update_data_after_hand_delete_meter
from sql.model import (
    EquipmentHandModelUpdate,
    LogHandModelSet,
    MeterDelHandModelDel,
    MeterDelHandModelSet,
    MeterDelHandModelUpdate,
    TaskHandModelUpdate,
)


async def hand_result_del(result_in: GetComandModel):
    start_time = datetime.now()
    print(f'{datetime.now()}: start write data for task {result_in.task_id}')
    # при обновлении таски брать все даже None
    task = hand_task(result_in)
    equipment = hand_equipment(result_in)
    meter = await hand_meter(result_in)
    log = hand_log(result_in)

    await update_data_after_hand_delete_meter(task, equipment, meter, log)

    end_time = datetime.now()
    delta = end_time - start_time
    total_time = round(delta.total_seconds())

    print(f'{datetime.now()}: stop write data for task {result_in.task_id}, , total time {total_time}')


def get_str_eui_hand(result_in: GetComandModel, meter: str) -> str:
    """функция добавляет новые meter_true к уже существующим meter_true с проверкой начилия ПУ в БС"""
    if result_in.meter_wl_del.empty_wl is True:
        meter = result_in.meter_wl_del.list_meter_del
    else:
        for line in result_in.meter_wl_del.meter_wl:
            if line.status is True:
                meter = meter + line.eui + ','
    return meter


def hand_task(result_in: GetComandModel) -> TaskHandModelUpdate:
    meter_true = '' if result_in.meter_true is None else result_in.meter_true
    if result_in.meter_wl_del is not None and result_in.meter_wl_del.meter_wl is not None:
        meter_true = get_str_eui_hand(result_in, meter_true)

    result = TaskHandModelUpdate(
        task_id=result_in.task_id,
        status_task=result_in.status_task,
        total_time=result_in.total_time,
        timeouut_task=timeout_task[result_in.type_task],
        error=result_in.error,
        meter_true=meter_true,
    )

    return result


def hand_equipment(result_in: GetComandModel) -> EquipmentHandModelUpdate | None:
    if result_in.equipment_info is not None and result_in.equipment_info.status is True:
        result = EquipmentHandModelUpdate(
            equipment_id=result_in.equipment_id,
            serial=result_in.equipment_info.serial,
            fw_version=result_in.equipment_info.fw_version,
            type_equipment=result_in.equipment_info.type_equipment,
            modification=result_in.equipment_info.modification,
            date_response=result_in.equipment_info.date_response,
        )
        return result
    else:
        return None


async def hand_meter(
    result_in: GetComandModel,
) -> dict[list[MeterDelHandModelUpdate], list[MeterDelHandModelSet], list[MeterDelHandModelDel]]:
    dict_result = {
        'update_meter': [],
        'create_meter': [],
        'delete_meter': [],
    }
    if result_in.meter_wl_del is not None:
        if result_in.meter_wl_del.empty_wl is False and result_in.meter_wl_del.meter_wl is not None:
            meter_del = [metrer_del.eui for metrer_del in result_in.meter_wl_del.meter_wl]
            meter_from_db = await get_meter_del_filter(meter_del, result_in.equipment_id)
            for line_md in result_in.meter_wl_del.meter_wl:
                trigger_meter_wl_del = 0
                for line_mfd in meter_from_db:
                    if line_md.eui == line_mfd.eui and line_md.status is True and line_mfd.delete_status is False:
                        dict_result['update_meter'].append(
                            MeterDelHandModelUpdate(meter_del_id=line_mfd.meter_del_id, delete_status=True)
                        )
                        trigger_meter_wl_del = 1
                        break
                if trigger_meter_wl_del == 0:
                    dict_result['create_meter'].append(
                        MeterDelHandModelSet(
                            equipment_id=result_in.equipment_id,
                            id_wl=line_md.id_wl,
                            eui=line_md.eui,
                            delete_status=line_md.status,
                        )
                    )
        meter_db_eui = set([sel_line_mfd.eui for sel_line_mfd in meter_from_db])
        delete_meter = meter_db_eui - set(meter_del)
        if len(delete_meter) > 0:
            dict_result['delete_meter'] = list(delete_meter)
    return dict_result


def hand_log(result_in: GetComandModel) -> LogHandModelSet:
    response = []

    if result_in.meter_wl_del is not None:
        response = result_in.meter_wl_del.model_dump_json()

    status_response = bool(len(response))

    result = LogHandModelSet(
        task_id=result_in.task_id,
        equipment_id=result_in.equipment_id,
        status_response=status_response,
        response=str(response),
    )

    return result
