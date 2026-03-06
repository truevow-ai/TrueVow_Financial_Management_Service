"""Payment Batch API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.core.database import get_db_session
from app.modules.payroll.services.payment_batch_service import PaymentBatchService
from app.modules.payroll.models.payment_batch_model import BatchStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.auth.authorization import get_user_context

router = APIRouter(prefix="/books/{book_id}/payroll", tags=["Payment Batches"], dependencies=[Depends(get_user_context)])


@router.post("/runs/{run_id}/wps-batch", status_code=status.HTTP_201_CREATED)
async def generate_wps_batch(
    book_id: UUID,
    run_id: UUID,
    exported_by: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Generate WPS payment batch"""
    service = PaymentBatchService(db)
    try:
        batch = await service.generate_wps_batch(run_id, exported_by)
        return {
            "batch_id": str(batch.id),
            "batch_number": batch.batch_number,
            "export_type": batch.export_type,
            "status": batch.status.value,
            "file_size": batch.file_size
        }
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/batches/{batch_id}/download")
async def download_batch_file(
    batch_id: UUID,
    db: AsyncSession = Depends(get_db_session)
):
    """Download payment batch file"""
    service = PaymentBatchService(db)
    batch = await service.batch_repo.get_by_id(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    file_content = await service.get_batch_file(batch_id)
    if not file_content:
        raise HTTPException(status_code=404, detail="Batch file not found")
    
    return Response(
        content=file_content,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={batch.batch_number}.sif"
        }
    )
