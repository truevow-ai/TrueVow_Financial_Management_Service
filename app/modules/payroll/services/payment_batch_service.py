"""Payment Batch Service - Generate payment batches"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from app.modules.payroll.repositories.payroll_run_repository import PayrollRunRepository, PayrollRunItemRepository
from app.modules.payroll.repositories.employee_repository import HREmployeeRepository
from app.modules.payroll.repositories.payment_batch_repository import PayrollPaymentBatchRepository
from app.modules.payroll.plugins.wps_export import UAEWPSExporter
from app.modules.payroll.models.payment_batch_model import PayrollPaymentBatch, BatchStatus
from app.modules.payroll.models.payroll_run_model import PayrollRunStatus
from app.core.exceptions import NotFoundError, ValidationError


class PaymentBatchService:
    """Service for generating payment batches"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.run_repo = PayrollRunRepository(session)
        self.item_repo = PayrollRunItemRepository(session)
        self.employee_repo = HREmployeeRepository(session)
        self.batch_repo = PayrollPaymentBatchRepository(session)
        self.wps_exporter = UAEWPSExporter()
    
    async def generate_wps_batch(
        self,
        payroll_run_id: UUID,
        exported_by: UUID
    ) -> PayrollPaymentBatch:
        """Generate WPS payment batch"""
        run = await self.run_repo.get_by_id(payroll_run_id)
        if not run:
            raise NotFoundError(f"Payroll run {payroll_run_id} not found")
        
        if run.status != PayrollRunStatus.POSTED:
            raise ValidationError(f"Cannot generate batch for run with status {run.status.value}")
        
        # Get run items
        items = await self.item_repo.list_by_run(payroll_run_id)
        
        # Prepare employee data
        employees = []
        for item in items:
            employee = await self.employee_repo.get_by_id(item.hr_employee_id)
            if not employee or not employee.wps_enabled:
                continue
            
            # Validate employee data
            emp_data = {
                "labour_id": employee.labour_id,
                "mol_id": employee.mol_id,
                "iban": employee.iban or (employee.bank_details[0].iban if employee.bank_details else ""),
                "net_pay": item.net_pay,
                "currency": item.currency,
                "reference": f"PR-{run.run_number}-{employee.employee_code}"
            }
            
            is_valid, error = self.wps_exporter.validate_employee_data(emp_data)
            if not is_valid:
                continue  # Skip invalid employees
            
            employees.append(emp_data)
        
        if not employees:
            raise ValidationError("No valid WPS employees found in payroll run")
        
        # Generate SIF file
        sif_content = self.wps_exporter.generate_sif_file(
            payroll_run_id=payroll_run_id,
            employees=employees,
            pay_date=run.pay_date
        )
        
        # Calculate file hash
        import hashlib
        file_hash = hashlib.sha256(sif_content).hexdigest()
        
        # Generate batch number
        batch_number = f"WPS-{run.run_number}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create batch record
        batch = await self.batch_repo.create(
            payroll_run_id=payroll_run_id,
            batch_number=batch_number,
            export_type="WPS_SIF",
            status=BatchStatus.GENERATED,
            file_hash=file_hash,
            file_size=len(sif_content),
            exported_by=exported_by,
            exported_at=datetime.now()
        )
        
        await self.session.commit()
        return batch
    
    async def get_batch_file(
        self,
        batch_id: UUID
    ) -> Optional[bytes]:
        """Get batch file content"""
        batch = await self.batch_repo.get_by_id(batch_id)
        if not batch:
            return None
        
        # In production, would read from file storage
        # For now, regenerate if needed
        if batch.export_type == "WPS_SIF":
            run = await self.run_repo.get_by_id(batch.payroll_run_id)
            items = await self.item_repo.list_by_run(batch.payroll_run_id)
            
            employees = []
            for item in items:
                employee = await self.employee_repo.get_by_id(item.hr_employee_id)
                if employee and employee.wps_enabled:
                    employees.append({
                        "labour_id": employee.labour_id,
                        "mol_id": employee.mol_id,
                        "iban": employee.iban or "",
                        "net_pay": item.net_pay,
                        "currency": item.currency,
                        "reference": f"PR-{run.run_number}-{employee.employee_code}"
                    })
            
            return self.wps_exporter.generate_sif_file(
                payroll_run_id=batch.payroll_run_id,
                employees=employees,
                pay_date=run.pay_date
            )
        
        return None
