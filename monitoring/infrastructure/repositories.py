from typing import Optional
import peewee
from monitoring.domain.repositories import IPropertyAssetRepository
from monitoring.domain.entities import PropertyAsset
from monitoring.infrastructure.models import PropertyAssetStateModel


class PeeweePropertyAssetRepository(IPropertyAssetRepository):

    def find_by_device_id(self, device_id: str) -> Optional[PropertyAsset]:
        try:
            row = PropertyAssetStateModel.get(PropertyAssetStateModel.device_id == device_id)
            return PropertyAsset(
                device_id=row.device_id,
                apartment_id=row.apartment_id,
                is_security_mode_armed=row.is_security_mode_armed,
                is_valve_closed=row.is_valve_closed,
                is_door_locked=row.is_door_locked
            )
        except peewee.DoesNotExist:
            return None

    def save(self, asset: PropertyAsset) -> PropertyAsset:
        row, created = PropertyAssetStateModel.get_or_create(
            device_id=asset.device_id,
            defaults={
                "apartment_id": asset.apartment_id,
                "is_security_mode_armed": asset.is_security_mode_armed,
                "is_valve_closed": asset.is_valve_closed,
                "is_door_locked": asset.is_door_locked
            }
        )
        if not created:
            row.is_security_mode_armed = asset.is_security_mode_armed
            row.is_valve_closed = asset.is_valve_closed
            row.is_door_locked = asset.is_door_locked
            row.save()
        return asset