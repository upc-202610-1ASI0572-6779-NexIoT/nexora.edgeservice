"""Domain entities for the monitoring bounded context.

This module defines the core domain models that represent the state and
business logic of the property monitoring system. The primary entity is the
``PropertyAsset``, which acts as an Aggregate Root.
"""
from datetime import datetime
from typing import Dict, Any, Optional

class PropertyAsset:
    """Represents the IoT control hub for a residential property at the edge.

    This class is the Aggregate Root for the monitoring context. It manages the
    state of actuators, security settings, and centralizes the processing of
    multi-variable sensor readings (e.g., Gas, Water, Motion). It encapsulates
    the core business rules for threat detection and prevention.

    Attributes:
        id (Optional[int]): The unique database identifier for the entity.
        device_id (str): The unique identifier of the physical IoT device.
        apartment_id (str): The identifier for the property unit (e.g., 'Apt-402').
        is_security_mode_armed (bool): Flag indicating if the intrusion alarm system is active.
        is_valve_closed (bool): State of the main gas/water valve.
        is_door_locked (bool): State of the smart door lock.
        water_flow_start_time (Optional[datetime]): Timestamp marking the beginning
            of a continuous water flow, used for waste detection.
    """

    def __init__(
        self,
        device_id: str,
        apartment_id: str,
        is_security_mode_armed: bool = False,
        is_valve_closed: bool = False,
        is_door_locked: bool = True,
        id: Optional[int] = None
    ):
        """Initialises the PropertyAsset aggregate.

        Args:
            device_id (str): The unique identifier of the physical IoT device.
            apartment_id (str): The identifier for the property unit.
            is_security_mode_armed (bool): Initial state of the security mode.
            is_valve_closed (bool): Initial state of the main valve.
            is_door_locked (bool): Initial state of the door lock.
            id (Optional[int]): The database ID, typically set by the repository.
        """
        self.id = id
        self.device_id = device_id
        self.apartment_id = apartment_id
        self.is_security_mode_armed = is_security_mode_armed
        self.is_valve_closed = is_valve_closed
        self.is_door_locked = is_door_locked
        self.water_flow_start_time: Optional[datetime] = None

    def process_telemetry(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Applies domain invariants based on an incoming IoT data payload.

        This method is the core of the domain logic, evaluating sensor data
        against a set of business rules to identify critical incidents (like
        gas leaks or intrusions) and preventative alerts (like resource waste).
        It determines the severity of the event and prescribes immediate
        tactical actions for actuators.

        Args:
            raw_data (Dict[str, Any]): A dictionary containing the telemetry
                payload from the IoT device. Expected keys include 'gas_ppm',
                'smoke_detected', 'motion_detected', etc.

        Returns:
            Dict[str, Any]: A dictionary containing the analysis result,
            including the event's severity, an alert type, a descriptive
            message, and a dictionary of commands for actuators (e.g.,
            ``{'valve_command': 'CLOSE'}``).
        """
        gas_ppm = float(raw_data.get("gas_ppm", 0.0))
        water_flow = float(raw_data.get("water_flow", 0.0)) # in liters/min
        is_smoke_detected = bool(raw_data.get("smoke_detected", False))
        is_motion_detected = bool(raw_data.get("motion_detected", False))
        is_door_open = bool(raw_data.get("door_open", False))

        actions = {"valve_command": "KEEP_OPEN", "door_command": "KEEP_STATE"}
        severity = "OK"
        alert_type = None
        message = "System operational"

        # 1. INVARIANT: Critical Incidents (Red Level)
        if gas_ppm >= 400.0 or is_smoke_detected:
            self.is_valve_closed = True
            actions["valve_command"] = "CLOSE"
            severity = "CRITICAL_INCIDENT"
            alert_type = "FIRE_GAS_EMERGENCY"
            message = "High concentration of flammable risk/smoke detected. Valve has been closed."
            return {"severity": severity, "alert_type": alert_type, "message": message, "actions": actions}

        if self.is_security_mode_armed and (is_motion_detected or is_door_open):
            severity = "CRITICAL_INCIDENT"
            alert_type = "INTRUSION_DETECTED"
            message = "Perimeter intrusion detected in an unoccupied, armed property."
            return {"severity": severity, "alert_type": alert_type, "message": message, "actions": actions}

        # 2. INVARIANT: Prevention Alerts (Yellow Level)
        if gas_ppm > 50.0 and gas_ppm < 400.0:
            severity = "PREVENTION"
            alert_type = "MICRO_LEAK_GAS"
            message = "Anomalous minor variation detected in kitchen gas sensors."

        elif water_flow > 0.0:
            # Local logic for water leak/waste control (e.g., tap open > 15 mins)
            if not self.water_flow_start_time:
                self.water_flow_start_time = datetime.utcnow()
            else:
                elapsed_minutes = (datetime.utcnow() - self.water_flow_start_time).total_seconds() / 60.0
                if elapsed_minutes >= 15.0:
                    severity = "PREVENTION"
                    alert_type = "WATER_WASTE_ALERT"
                    message = "Continuous water flow detected for over 15 minutes in the unit."
        else:
            self.water_flow_start_time = None # Reset water flow timer

        return {
            "severity": severity,
            "alert_type": alert_type,
            "message": message,
            "actions": actions
        }

    def change_security_mode(self, arm: bool):
        """Enables or disables the Security Mode for an unoccupied property.

        Args:
            arm (bool): ``True`` to arm the system, ``False`` to disarm.
        """
        self.is_security_mode_armed = arm

    def execute_remote_lock(self, lock: bool):
        """Changes the state of the smart lock.

        Args:
            lock (bool): ``True`` to lock the door, ``False`` to unlock.
        """
        self.is_door_locked = lock
