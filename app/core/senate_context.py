"""
Singleton context for SenateDataSource in Valet.
"""
from app.datasources.senate import SenateDataSource, SenateDataUnavailableError
import os

class SenateContext:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            try:
                cls._instance = SenateDataSource(data_dir=os.environ.get("SENATE_DATA_DIR"))
            except SenateDataUnavailableError:
                cls._instance = None
        return cls._instance
