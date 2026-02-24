from app.audit.rules import audit_vote_claim, audit_dataset
from app.datasources.senate.senate_datasource import SenateDataSource
from app.audit.types import AuditResult, AuditStatus

def run_vote_audit(senate: SenateDataSource, senator_id: str, bill_id: str) -> AuditResult:
    try:
        return audit_vote_claim(senate, senator_id, bill_id)
    except Exception as e:
        return AuditResult(status=AuditStatus.INVALID_DATA, checks=[{"error": str(e)}])

def run_dataset_audit(senate: SenateDataSource) -> AuditResult:
    try:
        return audit_dataset(senate)
    except Exception as e:
        return AuditResult(status=AuditStatus.INVALID_DATA, checks=[{"error": str(e)}])
