import json
from datetime import datetime

from base_http.base import BaseRequest
from data_class.data_get_command import (
    EquipmentInfoModel,
    MeterWlAllModel,
    MeterWlModel,
)


async def get_tzcode(con: BaseRequest, token: str) -> int | None:
    """Функция запрапшивает часовой пояс УСПД, если вернет None, то это не штатная ситуация"""
    result = None
    tzcode = await con.get_request('tzcode', token)
    try:
        if tzcode.status is True:
            tzcode.data = json.loads(tzcode.data)
            result = tzcode.data['timezone']
        else:
            result = None
    except:
        result = None
    return result


async def get_dev_info(con: BaseRequest, token: str) -> EquipmentInfoModel | None:
    """Функция запропшивает информацию об УСПД, если вернет None, то это не штатная ситуация"""
    result = None
    equipment_info = await con.get_request('devinfo', token)
    date_now = datetime.now()
    try:
        if equipment_info.status is True:
            equipment_info.data = json.loads(equipment_info.data)
            result = EquipmentInfoModel(
                status=True,
                serial=equipment_info.data['serial'],
                fw_version=equipment_info.data['uspd_update_version'],
                type_equipment=equipment_info.data['name'],
                modification=equipment_info.data['modification'],
                date_response=date_now,
            )
        else:
            result = EquipmentInfoModel(status=False, error=str(equipment_info.error), date_response=date_now)
    except Exception as ex:
        result = EquipmentInfoModel(status=False, error=str(ex.args), date_response=date_now)
    return result


async def get_wl(con: BaseRequest, token: str) -> MeterWlAllModel | None:
    """Функция запропшивает ПУ из БС, если вернет None, то это не штатная ситуация"""
    result = None
    meter_wl = await con.get_request('devices', token)
    try:
        if meter_wl.status is True:
            result = MeterWlAllModel(status=True)
            meter_wl.data = json.loads(meter_wl.data)
            if len(meter_wl.data) > 0:
                result.meter_wl = []
                for line in meter_wl.data:
                    result.meter_wl.append(
                        MeterWlModel(
                            id_wl=line['id'],
                            eui=line['eui'],
                            archive=line['archive'],
                            included_in_survey=line['included_in_survey'],
                        )
                    )
        else:
            result = MeterWlAllModel(status=False, error=str(meter_wl.error))
    except Exception as ex:
        result = MeterWlAllModel(status=False, error=str(ex.args))

    return result
