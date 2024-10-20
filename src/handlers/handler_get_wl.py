from asyncio import sleep
from datetime import datetime, timedelta
from random import randint

from config import timeout_task
from data_class.data_get_command import GetComandModel
from db_handler import (
    get_meter_new_filter,
    get_wl_filter_equipment,
    set_meter_new,
    update_data_after_hand_get_wl,
)
from sql.model import (
    EquipmentHandModelUpdate,
    LogHandModelSet,
    MeterNewModelSet,
    MeterWLModelSet,
    MeterWLModelUpdate,
    TaskHandModelUpdate,
)


async def hand_result_get_wl(result_in: GetComandModel):
    start_time = datetime.now()
    print(f'{datetime.now()}: start write data for task {result_in.task_id}')
    # при обновлении таски брать все даже None
    task = hand_task(result_in)
    equipment = hand_equipment(result_in)
    meter = await hand_meter(result_in)
    log = hand_log(result_in)

    for _ in range(1, 10, 1):
        result_wr = await update_data_after_hand_get_wl(task, equipment, meter, log)
        if result_wr is not None:
            sleep(randint(1, 5))
            print(f'---------Ошибка при записи в БД {result_wr} спим')
            result_wr = await update_data_after_hand_get_wl(task, equipment, meter, log)
            if result_wr is None:
                break
        else:
            break

    end_time = datetime.now()
    delta = end_time - start_time
    total_time = round(delta.total_seconds())

    print(f'{datetime.now()}: stop write data for task {result_in.task_id}, , total time {total_time}')


def hand_task(result_in: GetComandModel) -> TaskHandModelUpdate:
    result = TaskHandModelUpdate(
        task_id=result_in.task_id,
        status_task=result_in.status_task,
        total_time=result_in.total_time,
        timeouut_task=timeout_task[result_in.type_task],
        error=result_in.error,
        meter_true=None,
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


async def set_meter_new_from_wl(meter_from_wl: list):
    meter_from_db = await get_meter_new_filter(meter_from_wl)
    eui_from_db = set([line_mfwl.eui for line_mfwl in meter_from_db])
    meter_for_db = set(meter_from_wl) - eui_from_db
    result_set_meter_new = None
    if len(meter_for_db) > 0:
        list_add_meter = []
        for line_mfdb in meter_for_db:
            list_add_meter.append(MeterNewModelSet(eui=line_mfdb))
        result_set_meter_new = await set_meter_new(list_add_meter)
    return result_set_meter_new


async def hand_meter(
    result_in: GetComandModel,
) -> dict[list[MeterWLModelUpdate], list[MeterWLModelSet]]:
    dict_result = {
        'update_wl': [],
        'create_wl': [],
    }
    if result_in.meter_wl_wl is not None and result_in.meter_wl_wl.status is True:
        wl_from_db = await get_wl_filter_equipment(result_in.equipment_id)
        if result_in.meter_wl_wl.meter_wl is not None and len(result_in.meter_wl_wl.meter_wl) > 0:
            meter_from_wl = [metrer_wl.eui for metrer_wl in result_in.meter_wl_wl.meter_wl]

            for _ in range(1, 10, 1):
                result_set_meter_new = await set_meter_new_from_wl(meter_from_wl)
                if result_set_meter_new is not None:
                    sleep(randint(1, 5))
                    print(f'---------Ошибка при записи в БД {result_set_meter_new} спим')
                    result_set_meter_new = await set_meter_new_from_wl(meter_from_wl)
                    if result_set_meter_new is None:
                        break
                else:
                    break

            meter_from_db = await get_meter_new_filter(meter_from_wl)

            for line_wl in result_in.meter_wl_wl.meter_wl:
                trigger_wl = 0
                for line_wlfd in wl_from_db:
                    if line_wl.eui == line_wlfd.eui:
                        temp_update = MeterWLModelUpdate(wl_id=line_wlfd.wl_id)
                        if line_wl.id_wl_in_uspd != line_wlfd.id_wl_in_uspd:
                            temp_update.id_wl_in_uspd = line_wl.id_wl_in_uspd
                        if line_wlfd.present is False:
                            temp_update.present = True
                        if line_wl.archive != line_wlfd.archive:
                            temp_update.archive = line_wl.archive
                        if line_wl.included_in_survey != line_wlfd.included_in_survey:
                            temp_update.included_in_survey = line_wl.included_in_survey
                        if line_wl.added != line_wlfd.added + timedelta(hours=result_in.time_zone):
                            temp_update.added = line_wl.added + timedelta(hours=result_in.time_zone)
                        if line_wl.added != line_wlfd.added:
                            temp_update.added = line_wl.added
                        if line_wl.id_interface != line_wlfd.id_interface:
                            temp_update.id_interface = line_wl.id_interface
                        if line_wl.id_model != line_wlfd.id_model:
                            temp_update.id_model = line_wl.id_model

                        if line_wlfd.last_success_time is not None:
                            if line_wl.last_success_time != line_wlfd.last_success_time + timedelta(
                                hours=result_in.time_zone
                            ):
                                temp_update.last_success_time = line_wl.last_success_time + timedelta(
                                    hours=result_in.time_zone
                                )
                        else:
                            temp_update.last_success_time = None

                        if line_wl.name != line_wlfd.name:
                            temp_update.name = line_wl.name
                        if line_wl.mod_name != line_wlfd.mod_name:
                            temp_update.mod_name = line_wl.mod_name
                        if line_wl.serial != line_wlfd.serial:
                            temp_update.serial = line_wl.serial
                        if line_wl.res_name != line_wlfd.res_name:
                            temp_update.res_name = line_wl.res_name
                        trigger_wl = 1

                        dict_temp_update = temp_update.__dict__
                        count_none = 0
                        for line_dtu in dict_temp_update.values():
                            if line_dtu is not None:
                                count_none += 1
                        if count_none > 1:
                            dict_result['update_wl'].append(temp_update)
                        break
                if trigger_wl == 0:
                    for line_mfdb in meter_from_db:
                        if line_wl.eui == line_mfdb.eui:
                            meter_new_id = line_mfdb.meter_new_id
                            break
                    dict_result['create_wl'].append(
                        MeterWLModelSet(
                            equipment_id=result_in.equipment_id,
                            meter_new_id=meter_new_id,
                            id_wl_in_uspd=line_wl.id_wl_in_uspd,
                            present=True,
                            archive=line_wl.archive,
                            included_in_survey=line_wl.included_in_survey,
                            added=line_wl.added,
                            id_interface=line_wl.id_interface,
                            id_model=line_wl.id_model,
                            last_success_time=line_wl.last_success_time,
                            name=line_wl.name,
                            mod_name=line_wl.mod_name,
                            serial=line_wl.serial,
                            res_name=line_wl.res_name,
                        )
                    )

            eui_for_del = set([line_wlfdb.eui for line_wlfdb in wl_from_db]) - set(meter_from_wl)
            for line_efd in eui_for_del:
                for line_wlfdb in wl_from_db:
                    if line_efd == line_wlfdb.eui:
                        dict_result['update_wl'].append(MeterWLModelUpdate(wl_id=line_wlfdb.wl_id, present=False))
                        break
        else:
            for line_wlfdb in wl_from_db:
                dict_result['update_wl'].append(MeterWLModelUpdate(wl_id=line_wlfdb.wl_id, present=False))

    return dict_result


def hand_log(result_in: GetComandModel) -> LogHandModelSet:
    response = []

    if result_in.meter_wl_wl is not None:
        response = result_in.meter_wl_wl.model_dump_json()

    status_response = bool(len(response))

    result = LogHandModelSet(
        task_id=result_in.task_id,
        equipment_id=result_in.equipment_id,
        status_response=status_response,
        response=str(response),
    )

    return result
