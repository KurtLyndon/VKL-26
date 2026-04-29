from sqlalchemy import delete, select

from app.db.session import SessionLocal
from app.models import (
    FindingAsset,
    GeneratedReport,
    OperationExecution,
    OperationResultImportExport,
    ReportSnapshot,
    ScanImportBatch,
    ScanResult,
    ScanResultFinding,
    Target,
    TaskExecution,
)


SYSTEM_TARGET_CODES = {"target_unmapped_historical"}


def reset_runtime_data() -> None:
    db = SessionLocal()
    try:
        db.execute(delete(ReportSnapshot))
        db.execute(delete(GeneratedReport))
        db.execute(delete(FindingAsset))
        db.execute(delete(ScanResultFinding))
        db.execute(delete(ScanResult))
        db.execute(delete(ScanImportBatch))
        db.execute(delete(TaskExecution))
        db.execute(delete(OperationExecution))
        db.execute(delete(OperationResultImportExport))

        system_targets = db.scalars(select(Target).where(Target.code.in_(SYSTEM_TARGET_CODES))).all()
        for target in system_targets:
            db.delete(target)

        db.commit()
        print("Reset runtime/import/demo data completed.")
    finally:
        db.close()


if __name__ == "__main__":
    reset_runtime_data()
