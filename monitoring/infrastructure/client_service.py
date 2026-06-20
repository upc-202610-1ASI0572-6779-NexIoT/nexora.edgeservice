import requests
import threading
import time


class CloudSaaSGatewayClient:
    """Asynchronous component for unified synchronization to the Cloud Backend.

    Takes the total data packet processed at the Edge and sends it in a block
    via HTTP POST to the internet to feed the Nexora Web App and Mobile App.
    """

    def __init__(self):
        # Unified endpoint of the central Cloud Backend
        # self.cloud_sync_url = "https://api.nexora-platform.com/api/v1/telemetry"
        self.cloud_sync_url = "http://localhost:5001/api/v1/telemetry"
        # Start the background sync loop for offline resilience
        self._start_background_sync_loop()

    def _start_background_sync_loop(self):
        worker = threading.Thread(target=self._background_sync_loop)
        worker.daemon = True
        worker.start()

    def _background_sync_loop(self):
        """Periodically scans SQLite for unsynced records and attempts to send them."""
        # Wait a bit on startup to let the app initialize
        time.sleep(5)
        while True:
            try:
                from monitoring.infrastructure.models import TelemetryRecordModel

                # Fetch unsynced records
                unsynced = list(TelemetryRecordModel.select().where(TelemetryRecordModel.is_synced == False).order_by(
                    TelemetryRecordModel.created_at.asc()))

                for record in unsynced:
                    self._sync_record(record)
            except Exception:
                # Suppress exceptions in background thread to prevent crash
                pass
            time.sleep(30)

    def dispatch_record_async(self, record_id: int):
        """Triggers an independent thread of execution to sync a specific record immediately."""
        worker = threading.Thread(target=self._execute_single_sync, args=(record_id,))
        worker.daemon = True
        worker.start()

    def _execute_single_sync(self, record_id: int):
        try:
            from monitoring.infrastructure.models import TelemetryRecordModel
            record = TelemetryRecordModel.get_by_id(record_id)
            self._sync_record(record)
        except Exception:
            pass

    def _sync_record(self, record) -> bool:
        """Sends a single telemetry record to the cloud and updates database state on success."""
        try:
            # Construct payload matching TelemetryPayloadDto
            unix_timestamp = int(record.created_at.timestamp())
            payload = {
                "deviceId": record.device_id,
                "timestamp": unix_timestamp,
                "sensors": {
                    "waterLpm": float(record.water_flow),
                    "gasPpm": float(record.gas_ppm),
                    "presence": int(record.presence),
                    "electricityKwh": float(record.electricity_kwh),
                    "voltageOk": bool(getattr(record, 'voltage_ok', True))
                }
            }
            # Transparent synchronization via REST API
            response = requests.post(self.cloud_sync_url, json=payload, timeout=4)
            if response.status_code == 201:
                # Update record in DB
                record.is_synced = True
                record.save()
                print(f"[EDGE-TO-CLOUD SUCCESS] Payload indexed in the cloud for device {record.device_id}")
                return True
            else:
                print(
                    f"[EDGE-TO-CLOUD FAILURE] Backend returned status code {response.status_code} for device {record.device_id}")
                return False
        except requests.exceptions.RequestException:
            print(f"[CLOUD SYNC OFFLINE] Edge disconnected from the cloud. Record {record.id} preserved locally.")
            return False