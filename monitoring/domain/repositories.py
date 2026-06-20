from abc import ABC, abstractmethod
from typing import Optional
from monitoring.domain.entities import PropertyAsset

class IPropertyAssetRepository(ABC):
    @abstractmethod
    def find_by_device_id(self, device_id: str) -> Optional[PropertyAsset]:
        pass

    @abstractmethod
    def save(self, asset: PropertyAsset) -> PropertyAsset:
        pass