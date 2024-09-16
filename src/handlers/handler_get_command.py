from datetime import datetime

from config import timeout_task
from data_class.data_get_command import GetComandModel
from db_handler import get_meter_filter, update_data_after_hand
from sql.model import (
    EquipmentHandModelUpdate,
    LogHandModelSet,
    MeterHandModelSet,
    MeterModelUpdate,
    TaskHandModelUpdate,
)


async def hand_result(result_in: GetComandModel):
    start_time = datetime.now()
    print(f'{datetime.now()}: start write data for task {result_in.task_id}')
    # при обновлении таски брать все даже None
    task = hand_task(result_in)
    equipment = hand_equipment(result_in)
    meter = await hand_meter(result_in)
    log = hand_log(result_in)

    await update_data_after_hand(task, equipment, meter, log)

    end_time = datetime.now()
    delta = end_time - start_time
    total_time = round(delta.total_seconds())

    print(f'{datetime.now()}: stop write data for task {result_in.task_id}, , total time {total_time}')


def get_str_eui_hand(result_in: GetComandModel, meter) -> str:
    for line in result_in.meter_wl.meter_wl:
        if line.task_hand_log is not None and line.task_hand_log.status_task_db == 'true':
            meter = meter + line.eui + ','
    return meter


def get_str_eui_meter(result_in: GetComandModel, meter) -> str:
    for line in result_in.meter_wl.meter_wl:
        meter = meter + line.eui + ','
    return meter


def hand_task(result_in: GetComandModel) -> TaskHandModelUpdate:
    meter_true = '' if result_in.meter_true is None else result_in.meter_true
    if (
        result_in.meter_wl is not None
        and result_in.meter_wl.status is True
        and result_in.meter_wl.meter_wl is not None
        and len(result_in.meter_wl.meter_wl) > 0
    ):
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


async def hand_meter(result_in: GetComandModel) -> dict[list[MeterHandModelSet], list[MeterModelUpdate]]:
    dict_result = {
        'update_meter': [],
        'create_meter': [],
    }
    if (
        result_in.meter_wl is not None
        and result_in.meter_wl.status is True
        and result_in.meter_wl.meter_wl is not None
        and len(result_in.meter_wl.meter_wl) > 0
    ):
        str_meter = get_str_eui_meter(result_in, '')
        list_meter = str_meter.split(',')
        meter_from_db = await get_meter_filter(list_meter)

        meter_update = []
        if len(meter_from_db) > 0:
            for line_mfd in meter_from_db:
                if result_in.equipment_id == line_mfd.equipment_id:
                    temp_dict = {'eui': line_mfd.eui, 'meter_id': line_mfd.meter_id}
                    meter_update.append(temp_dict)

        len_meter_update = len(meter_update)
        for line_mwl in result_in.meter_wl.meter_wl:
            trigger_meter_update = 0
            if len_meter_update > 0:
                for line_mu in meter_update:
                    if line_mu['eui'] == line_mwl.eui:
                        shedule = str(line_mwl.schedule) if line_mwl.schedule is not None else None
                        dict_result['update_meter'].append(
                            MeterModelUpdate(
                                meter_id=line_mu['meter_id'],
                                id_wl=line_mwl.id_wl,
                                archive=line_mwl.archive,
                                included_in_survey=line_mwl.included_in_survey,
                                schedule=shedule,
                                schedule_date=line_mwl.schedule_date,
                                schedule_status=line_mwl.schedule_status,
                                leave_time=line_mwl.leave_time,
                                leave_time_date=line_mwl.leave_time_date,
                                leave_time_status=line_mwl.leave_time_status,
                                tariff_mask=line_mwl.tariff_mask,
                                tariff_mask_date=line_mwl.tariff_mask_date,
                                tariff_mask_status=line_mwl.tariff_mask_status,
                            )
                        )
                        trigger_meter_update = 1
                        break
            if trigger_meter_update == 0:
                shedule = str(line_mwl.schedule) if line_mwl.schedule is not None else None
                dict_result['create_meter'].append(
                    MeterHandModelSet(
                        equipment_id=result_in.equipment_id,
                        id_wl=line_mwl.id_wl,
                        eui=line_mwl.eui,
                        archive=line_mwl.archive,
                        included_in_survey=line_mwl.included_in_survey,
                        schedule=shedule,
                        schedule_date=line_mwl.schedule_date,
                        schedule_status=line_mwl.schedule_status,
                        leave_time=line_mwl.leave_time,
                        leave_time_date=line_mwl.leave_time_date,
                        leave_time_status=line_mwl.leave_time_status,
                        tariff_mask=line_mwl.tariff_mask,
                        tariff_mask_date=line_mwl.tariff_mask_date,
                        tariff_mask_status=line_mwl.tariff_mask_status,
                    )
                )
    return dict_result


def hand_log(result_in: GetComandModel) -> LogHandModelSet:
    list_response = []

    if (
        result_in.meter_wl is not None
        and result_in.meter_wl.status is True
        and result_in.meter_wl.meter_wl is not None
        and len(result_in.meter_wl.meter_wl) > 0
    ):
        for line in result_in.meter_wl.meter_wl:
            temp_log = {
                'eui': line.eui,
                'task_log': '',
                'task_hand_log': '',
            }
            if line.task_log is not None:
                temp_log['task_log'] = str(line.task_log.model_dump_json())
            if line.task_hand_log is not None:
                temp_log['task_hand_log'] = str(line.task_hand_log.model_dump_json())
            list_response.append(temp_log)

    status_response = bool(len(list_response))

    result = LogHandModelSet(
        task_id=result_in.task_id,
        equipment_id=result_in.equipment_id,
        status_response=status_response,
        response=str(list_response),
    )

    return result
