from flask import Flask
from monitoring.interfaces.services import monitoring_api
from iam.interfaces.services import iam_api
from shared.infrastructure.database import db

app = Flask(__name__)
app.register_blueprint(iam_api)
app.register_blueprint(monitoring_api)

first_run = True

@app.before_request
def setup_edge_services():
    """Initialises the database and seeds required data on first request."""
    global first_run
    if first_run:
        first_run = False
        db.connect()
        from iam.infrastructure.models import Device as DeviceModel
        from monitoring.infrastructure.models import TelemetryRecordModel, PropertyAssetStateModel
        
        # Safe, idempotent initialisation in local SQLite
        db.create_tables([DeviceModel, TelemetryRecordModel, PropertyAssetStateModel], safe=True)
        
        # Seed the IAM test device
        from iam.application.services import AuthApplicationService
        auth_service = AuthApplicationService()
        auth_service.get_or_create_test_device()
        
        # db.close() is removed here to keep the connection open

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
