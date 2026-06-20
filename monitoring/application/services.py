"""Application services for the monitoring bounded context.

This module provides application services that orchestrate the use cases for
the IoT monitoring system. These services coordinate domain objects,
repositories, and external clients without containing any business logic themselves.
"""
from datetime import datetime
from typing import Dict, Any

from monitoring.domain.repositories import IPropertyAssetRepository
from monitoring.infrastructure.models import TelemetryRecordModel
from monitoring.infrastructure.client_service import CloudSaaSGatewayClient
from monitoring.domain.entities import PropertyAsset


class TelemetryApplicationService:
    """Orchestrates use cases for the unified Nexora IoT ecosystem.

    This service acts as a coordinator, handling incoming telemetry data,
    delegating business rule evaluation to the domain layer, persisting state,
    and dispatching information to external systems like the cloud backend.
    """

    def __init__(self, repository: IPropertyAssetRepository):
        """Initialises the service with its required dependencies.

        Args:
            repository (IPropertyAssetRepository): An implementation of the
                repository interface for accessing property asset data.
        """
        self.repository = repository
        self.cloud_client = CloudSaaSGatewayClient()

    def handle_incoming_telemetry(self, device_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Processes incoming telemetry data for a given device.

        This is the primary use case method. It retrieves the corresponding
        ``PropertyAsset`` aggregate, delegates the telemetry processing to it,
        persists the new state, logs the event, and dispatches the outcome to
        the cloud. It finally returns immediate action commands to the IoT device.

        Args:
            device_id (str): The unique identifier of the device sending the telemetry.
            payload (Dict[str, Any]): The raw telemetry data from the device.

        Returns:
            Dict[str, Any]: A response dictionary containing the processing
            status and any immediate actions to be executed by the device.
        """
        # 1. Safely retrieve or initialize the Domain Aggregate at the Edge
        asset = self.repository.find_by_device_id(device_id)
        if not asset:
            asset = PropertyAsset(device_id=device_id, apartment_id=payload.get("apartment_id", "Apt-Unknown"))

        # 2. Execute pure domain business logic (alerting invariants)
        evaluation = asset.process_telemetry(payload)

        # 3. Save the state of the Aggregate's actuators
        self.repository.save(asset)

        # 4. Log historical data locally for auditing and consumption metrics
        presence = 1 if (payload.get("motion_detected") or payload.get("door_open")) else 0
        record = TelemetryRecordModel.create(
            device_id=device_id,
            gas_ppm=float(payload.get("gas_ppm", 0.0)),
            water_flow=float(payload.get("water_flow", 0.0)),
            electricity_kwh=float(payload.get("electricity_kwh", 0.0)),
            water_m3=float(payload.get("water_m3", 0.0)),
            presence=presence,
            severity=evaluation["severity"],
            created_at=datetime.utcnow(),
            voltage_ok=bool(payload.get("voltaje_ok", True))
        )

        # 5. Dispatch the record to the Cloud Backend asynchronously
        self.cloud_client.dispatch_record_async(record.id)

        # Return immediate action directives in the HTTP response to the Embedded App
        return {
            "status": "PROCESSED",
            "valve_status": "CLOSED" if asset.is_valve_closed else "OPEN",
            "door_status": "LOCKED" if asset.is_door_locked else "UNLOCKED",
            "actions": evaluation["actions"]
        }

    def remote_toggle_security_mode(self, device_id: str, arm: bool) -> bool:
        """Use case triggered from the cloud to change the security mode.

        Finds the relevant property asset and delegates the state change to it,
        then persists the change.

        Args:
            device_id (str): The identifier of the target device.
            arm (bool): ``True`` to arm the security system, ``False`` to disarm.

        Returns:
            bool: ``True`` if the asset was found and updated, ``False`` otherwise.
        """
        asset = self.repository.find_by_device_id(device_id)
        if asset:
            asset.change_security_mode(arm)
            self.repository.save(asset)
            return True
        return False
