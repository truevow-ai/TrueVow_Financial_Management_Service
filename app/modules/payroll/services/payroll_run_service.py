"""Payroll Run Service - Workflow management"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.modules.payroll.repositories.payroll_run_repository import (
    PayrollRunRepository,
    PayrollRunItemRepository
)
from app.modules.payroll.repositories.pay_group_repository import PayGroupRepository
from app.modules.payroll.repositories.employee_repository import HREmployeeRepository
from app.modules.payroll.services.payroll_calculation_service import PayrollCalculationService
from app.modules.payroll.models.payroll_run_model import (
    PayrollRun,
    PayrollRunItem,
    PayrollRunComponentLine,
    PayrollRunStatus
)
from app.modules.general_ledger.services.ledger_poster import LedgerPoster, get_ledger_poster
from app.modules.general_ledger.repositories.gl_account_repository import GLAccountMappingRepository
from app.core.exceptions import NotFoundError, ValidationError


class PayrollRunService:
    """Service for payroll run workflow"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.run_repo = PayrollRunRepository(session)
        self.item_repo = PayrollRunItemRepository(session)
        self.pay_group_repo = PayGroupRepository(session)
        self.employee_repo = HREmployeeRepository(session)
        self.calc_service = PayrollCalculationService(session)
        self.je_service: LedgerPoster = get_ledger_poster(session)
        self.mapping_repo = GLAccountMappingRepository(session)
    
    async def create_run(
        self,
        entity_id: UUID,
        book_id: UUID,
        pay_group_id: UUID,
        pay_period_start: date,
        pay_period_end: date,
        pay_date: date
    ) -> PayrollRun:
        """Create a new payroll run"""
        # Verify pay group exists
        pay_group = await self.pay_group_repo.get_by_id(pay_group_id)
        if not pay_group:
            raise NotFoundError(f"Pay group {pay_group_id} not found")
        
        if pay_group.legal_entity_id != entity_id:
            raise ValidationError("Pay group must belong to the specified entity")
        
        # Generate run number
        run_number = await self._generate_run_number(entity_id, pay_period_end)
        
        # Create run
        run = await self.run_repo.create(
            legal_entity_id=entity_id,
            book_id=book_id,
            pay_group_id=pay_group_id,
            run_number=run_number,
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end,
            pay_date=pay_date,
            status=PayrollRunStatus.DRAFT,
            currency=pay_group.payroll_currency
        )
        
        await self.session.commit()
        return run
    
    async def calculate_run(
        self,
        run_id: UUID
    ) -> PayrollRun:
        """Calculate payroll run"""
        run = await self.run_repo.get_by_id(run_id)
        if not run:
            raise NotFoundError(f"Payroll run {run_id} not found")
        
        if run.status != PayrollRunStatus.DRAFT:
            raise ValidationError(f"Cannot calculate run with status {run.status.value}")
        
        # Get employees in pay group
        employees = await self.employee_repo.list_by_pay_group(
            pay_group_id=run.pay_group_id,
            active_only=True
        )
        
        total_gross = Decimal("0.00")
        total_deductions = Decimal("0.00")
        total_net = Decimal("0.00")
        total_employer_contrib = Decimal("0.00")
        
        # Calculate for each employee
        for employee in employees:
            calc_result = await self.calc_service.calculate_employee_pay(
                employee_id=employee.id,
                pay_period_start=run.pay_period_start,
                pay_period_end=run.pay_period_end
            )
            
            # Create run item
            run_item = await self.item_repo.create(
                payroll_run_id=run_id,
                hr_employee_id=employee.id,
                gross_pay=calc_result["gross_pay"],
                total_deductions=calc_result["total_deductions"],
                net_pay=calc_result["net_pay"],
                employer_contributions=calc_result["employer_contributions"],
                currency=calc_result["currency"]
            )
            
            # Create component lines
            for comp_line in calc_result["component_lines"]:
                component = await self._get_component_by_code(
                    run.legal_entity_id,
                    comp_line["component_code"]
                )
                if component:
                    await self._create_component_line(
                        run_item_id=run_item.id,
                        component_id=component.id,
                        amount=comp_line["amount"],
                        currency=calc_result["currency"]
                    )
            
            total_gross += calc_result["gross_pay"]
            total_deductions += calc_result["total_deductions"]
            total_net += calc_result["net_pay"]
            total_employer_contrib += calc_result["employer_contributions"]
        
        # Update run totals
        await self.run_repo.update(
            run_id,
            status=PayrollRunStatus.CALCULATED,
            total_gross=total_gross,
            total_deductions=total_deductions,
            total_net=total_net,
            total_employer_contrib=total_employer_contrib
        )
        
        await self.session.commit()
        return await self.run_repo.get_by_id(run_id)
    
    async def approve_run(
        self,
        run_id: UUID,
        approved_by: UUID
    ) -> PayrollRun:
        """Approve payroll run"""
        run = await self.run_repo.get_by_id(run_id)
        if not run:
            raise NotFoundError(f"Payroll run {run_id} not found")
        
        if run.status != PayrollRunStatus.CALCULATED:
            raise ValidationError(f"Cannot approve run with status {run.status.value}")
        
        await self.run_repo.update(
            run_id,
            status=PayrollRunStatus.APPROVED,
            approved_by=approved_by,
            approved_at=date.today()
        )
        
        await self.session.commit()
        return await self.run_repo.get_by_id(run_id)
    
    async def post_run(
        self,
        run_id: UUID,
        posted_by: UUID,
        row_version: Optional[int] = None
    ) -> UUID:
        """Post payroll run to ACCRUAL book"""
        run = await self.run_repo.get_by_id(run_id)
        if not run:
            raise NotFoundError(f"Payroll run {run_id} not found")
        
        # Check row_version for optimistic locking
        from app.core.row_version import check_row_version
        check_row_version(run.row_version, row_version, "payroll run")
        
        if run.status != PayrollRunStatus.APPROVED:
            raise ValidationError(f"Cannot post run with status {run.status.value}")
        
        # Get account mappings
        payroll_expense = await self._get_account_mapping(
            run.legal_entity_id,
            run.book_id,
            "EXP_PAYROLL"
        )
        payroll_liability = await self._get_account_mapping(
            run.legal_entity_id,
            run.book_id,
            "LIAB_PAYROLL"
        )
        employer_expense = await self._get_account_mapping(
            run.legal_entity_id,
            run.book_id,
            "EXP_EMPLOYER_CONTRIB"
        )
        
        # Get period
        from app.modules.general_ledger.repositories.accounting_period_repository import AccountingPeriodRepository
        period_repo = AccountingPeriodRepository(self.session)
        accounting_period = await period_repo.get_by_book_and_date(
            run.book_id,
            run.pay_date
        )
        if not accounting_period:
            raise NotFoundError(f"No period found for date {run.pay_date}")
        
        # Guard: Check if JE already exists with source_key (resilient to idempotency key misuse)
        source_key = f"PAYROLL:POST:{run_id}"
        from sqlalchemy import select
        from app.modules.general_ledger.models.journal_entry_model import JournalEntry, JournalEntryStatus
        existing_je = await self.session.execute(
            select(JournalEntry).where(
                JournalEntry.legal_entity_id == run.legal_entity_id,
                JournalEntry.book_id == run.book_id,
                JournalEntry.source_key == source_key,
                JournalEntry.status == JournalEntryStatus.POSTED
            )
        )
        existing_entry = existing_je.scalar_one_or_none()
        
        if existing_entry:
            # JE already posted - skip creation, proceed to update run state
            entry_id = existing_entry.id
        else:
            # Create journal entry
            entry = await self.je_service.create_draft_entry(
                book_id=run.book_id,
                entry_date=run.pay_date,
                description=f"Payroll run {run.run_number}: {run.pay_period_start} to {run.pay_period_end}",
                reference_number=run.run_number,
                source_service="payroll",
                source_type="payroll_run_posted",
                source_id=run.id,
                idempotency_key=f"payroll_run_{run.id}"
            )
            
            # Dr Payroll Expense (gross)
            await self.je_service.add_line(
                journal_entry_id=entry.id,
                gl_account_id=payroll_expense,
                debit_fc=run.total_gross,
                credit_fc=Decimal("0.00"),
                currency=run.currency
            )
            
            # Cr Payroll Liability (net)
            await self.je_service.add_line(
                journal_entry_id=entry.id,
                gl_account_id=payroll_liability,
                debit_fc=Decimal("0.00"),
                credit_fc=run.total_net,
                currency=run.currency
            )
            
            # Cr Payroll Liability (deductions)
            if run.total_deductions > 0:
                await self.je_service.add_line(
                    journal_entry_id=entry.id,
                    gl_account_id=payroll_liability,
                    debit_fc=Decimal("0.00"),
                    credit_fc=run.total_deductions,
                    currency=run.currency
                )
            
            # Dr Employer Contribution Expense
            if run.total_employer_contrib > 0:
                await self.je_service.add_line(
                    journal_entry_id=entry.id,
                    gl_account_id=employer_expense,
                    debit_fc=run.total_employer_contrib,
                    credit_fc=Decimal("0.00"),
                    currency=run.currency
                )
                
                await self.je_service.add_line(
                    journal_entry_id=entry.id,
                    gl_account_id=payroll_liability,
                    debit_fc=Decimal("0.00"),
                    credit_fc=run.total_employer_contrib,
                    currency=run.currency
                )
            
            # Post entry with source_key
            await self.je_service.post_entry(
                entry.id, 
                posted_by, 
                require_dimensions=False,
                source_key=source_key
            )
            entry_id = entry.id
        
        # Update run (increment row_version)
        run.row_version += 1
        await self.run_repo.update(
            run_id,
            status=PayrollRunStatus.POSTED,
            posted_by=posted_by,
            posted_at=date.today(),
            journal_entry_id=entry_id,
            row_version=run.row_version
        )
        
        await self.session.commit()
        return entry_id
    
    async def reverse_run(
        self,
        run_id: UUID,
        reversed_by: UUID,
        reason: str,
        reversal_date: Optional[date] = None
    ) -> PayrollRun:
        """
        Reverse a posted payroll run.
        
        Creates reversal journal entries and marks the run as REVERSED.
        If the original period is locked, reversal posts in the next open period.
        """
        run = await self.run_repo.get_by_id(run_id)
        if not run:
            raise NotFoundError(f"Payroll run {run_id} not found")
        
        if run.status != PayrollRunStatus.POSTED:
            raise ValidationError(
                f"Cannot reverse payroll run in status {run.status.value}. "
                "Must be POSTED."
            )
        
        if not run.journal_entry_id:
            raise ValidationError(
                "Payroll run has no associated journal entry. Cannot reverse."
            )
        
        # Reverse the journal entry (this handles period locking and creates reversal JE)
        reversal_source_key = f"PAYROLL:REVERSE:{run_id}"
        reversed_entry = await self.je_service.reverse_entry(
            journal_entry_id=run.journal_entry_id,
            reversed_by=reversed_by,
            reason=f"Payroll run reversal: {reason}",
            reversal_date=reversal_date,
            source_key=reversal_source_key
        )
        
        # Update run status to REVERSED
        # Store reversal reason in notes field (reversal_entry_id tracked via journal_entry relationship)
        reversal_note = f"Reversed: {reason}"
        if run.notes:
            reversal_note = f"{run.notes}\n{reversal_note}"
        
        await self.run_repo.update(
            run_id,
            status=PayrollRunStatus.REVERSED,
            notes=reversal_note
        )
        
        await self.session.commit()
        return await self.run_repo.get_by_id(run_id)
    
    async def _generate_run_number(
        self,
        entity_id: UUID,
        period_end: date
    ) -> str:
        """Generate unique run number"""
        date_str = period_end.strftime("%Y%m")
        return f"PR-{date_str}-{entity_id.hex[:8].upper()}"
    
    async def _get_component_by_code(
        self,
        entity_id: UUID,
        component_code: str
    ) -> Optional:
        """Get component by code"""
        from app.modules.payroll.repositories.pay_component_repository import PayComponentDefinitionRepository
        component_repo = PayComponentDefinitionRepository(self.session)
        return await component_repo.get_by_code(entity_id, component_code)
    
    async def _create_component_line(
        self,
        run_item_id: UUID,
        component_id: UUID,
        amount: Decimal,
        currency: str
    ) -> PayrollRunComponentLine:
        """Create component line"""
        from app.modules.payroll.repositories.payroll_run_repository import PayrollRunComponentLineRepository
        line_repo = PayrollRunComponentLineRepository(self.session)
        return await line_repo.create(
            payroll_run_item_id=run_item_id,
            pay_component_id=component_id,
            amount=amount,
            currency=currency
        )
    
    async def _get_account_mapping(
        self,
        entity_id: UUID,
        book_id: UUID,
        map_key: str
    ) -> UUID:
        """Get GL account from mapping"""
        mapping = await self.mapping_repo.get_mapping(entity_id, book_id, map_key)
        if not mapping:
            raise NotFoundError(f"Account mapping not found: {map_key}")
        return mapping.gl_account_id
