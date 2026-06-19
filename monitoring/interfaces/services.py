"""RESTful API endpoints for the monitoring bounded context.

This module defines the Flask blueprint and routes that expose the monitoring
application services to external clients, such as IoT devices and the cloud backend.
"""
from flask import Blueprint, request, jsonify
from monitoring.application.services import TelemetryApplicationService
from monitoring.infrastructure.repositories import PeeweePropertyAssetRepository
from iam.interfaces.services import authenticate_request

monitoring_api = Blueprint("monitoring_api", __name__)

# Dependency injection for the application service
asset_repository = PeeweePropertyAssetRepository()
telemetry_service = TelemetryApplicationService(asset_repository)

@monitoring_api.route("/api/v1/monitoring/telemetry", methods=["POST"])
def ingest_iot_telemetry():
    """Ingests telemetry data from an IoT device.

    This endpoint serves as the unified entry point for IoT devices to push
    their sensor readings to the edge service. It requires authentication via
    an API key.

    The request body must be a JSON object containing at least a 'device_id'
    and other relevant telemetry fields.

    .. sourcecode:: json

        {
            "device_id": "gas-safety-unit-apt-402",
            "apartment_id": "Apt-402",
            "gas_ppm": 450.5,
            "smoke_detected": true,
            ...
        }

    Returns:
        A JSON response with immediate action commands for the device and a
        status code:
        - 200: Telemetry processed successfully.
        - 400: Incomplete or malformed request payload.
        - 401/403: Authentication failure (handled by `authenticate_request`).
        - 500: Internal server error during processing.
    """
    # Cross-context authentication guard (IAM)
    auth_result = authenticate_request()
    if auth_result:
        return auth_result

    data = request.json
    if not data or "device_id" not in data:
        return jsonify({"error": "Incomplete or malformed payload"}), 400

    try:
        device_id = data["device_id"]
        # Unified processing
        response_data = telemetry_service.handle_incoming_telemetry(device_id, data)
        return jsonify(response_data), 200

    except ValueError as val_err:
        return jsonify({"error": str(val_err)}), 400
    except Exception as e:
        # It's good practice to log the exception 'e' here
        return jsonify({"error": "Internal error in edge processing"}), 500

@monitoring_api.route("/api/v1/monitoring/security-mode", methods=["PUT"])
def update_security_mode():
    """Updates the security mode for a property.

    This endpoint is exposed for a cloud backend or management interface to
    remotely arm or disarm the security system of a specific property.

    The request body must be a JSON object with 'device_id' and 'arm' fields.

    .. sourcecode:: json

        {
            "device_id": "gas-safety-unit-apt-402",
            "arm": true
        }

    Returns:
        A JSON response with a status code:
        - 200: Security mode updated successfully.
        - 400: Missing 'device_id' or 'arm' in the request.
        - 404: The specified device ID was not found.
    """
    data = request.json
    if not data or "device_id" not in data or "arm" not in data:
        return jsonify({"error": "Missing parameters"}), 400

    success = telemetry_service.remote_toggle_security_mode(data["device_id"], bool(data["arm"]))
    if success:
        return jsonify({"status": "Security mode updated successfully"}), 200
    return jsonify({"error": "Property device not found"}), 404
