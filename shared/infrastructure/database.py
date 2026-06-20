# src/shared/infrastructure/database.py
from peewee import SqliteDatabase

# Single instance of the local SQLite database for the Edge.
# The 'nexora_edge.db' file will be created in the project root.
db = SqliteDatabase('nexora_edge.db')


def init_db() -> None:
    """Opens the connection and idempotently creates the required tables.
    
    Performs deferred imports (at call time) to avoid circular dependencies
    between the IAM and Monitoring bounded contexts.
    """
    db.connect()
    
    # Deferred imports
    from iam.infrastructure.models import Device as DeviceModel
    from monitoring.infrastructure.models import TelemetryRecordModel, PropertyAssetStateModel
    
    # Create tables if they do not exist in the SQLite file
    db.create_tables([DeviceModel, TelemetryRecordModel, PropertyAssetStateModel], safe=True)
    db.close()
