"""
Custom errors for the Senate datasource adapter.
"""

class SenateDataSourceError(Exception):
    """Base error for SenateDataSource."""
    pass

class SenateDataUnavailableError(SenateDataSourceError):
    """Raised when the Senate data directory or required files are missing."""
    pass

class SenateDataValidationError(SenateDataSourceError):
    """Raised when a record fails schema validation."""
    pass
