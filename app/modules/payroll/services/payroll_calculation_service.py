"""Payroll Calculation Service"""
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.modules.payroll.repositories.employee_repository import HREmployeeRepository
from app.modules.payroll.repositories.pay_component_repository import (
    PayComponentDefinitionRepository,
    PayComponentAssignmentRepository
)
from app.modules.payroll.repositories.commission_repository import CommissionLedgerRepository
from app.modules.payroll.repositories.bonus_repository import BonusResultRepository
from app.modules.payroll.models.payroll_run_model import (
    PayrollRunItem,
    PayrollRunComponentLine
)
from app.modules.payroll.models.pay_component_model import ComponentType
from app.core.exceptions import NotFoundError, ValidationError


class PayrollCalculationService:
    """Service for calculating payroll"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.employee_repo = HREmployeeRepository(session)
        self.component_def_repo = PayComponentDefinitionRepository(session)
        self.component_assignment_repo = PayComponentAssignmentRepository(session)
        self.commission_ledger_repo = CommissionLedgerRepository(session)
        self.bonus_repo = BonusResultRepository(session)
    
    async def calculate_employee_pay(
        self,
        employee_id: UUID,
        pay_period_start: date,
        pay_period_end: date
    ) -> Dict:
        """Calculate pay for a single employee"""
        employee = await self.employee_repo.get_by_id(employee_id)
        if not employee:
            raise NotFoundError(f"Employee {employee_id} not found")
        
        if not employee.is_active:
            raise ValidationError(f"Employee {employee_id} is not active")
        
        # Get component assignments
        assignments = await self.component_assignment_repo.list_by_employee(
            employee_id=employee_id,
            effective_date=pay_period_end,
            active_only=True
        )
        
        # Calculate earnings
        earnings = Decimal("0.00")
        deductions = Decimal("0.00")
        employer_contrib = Decimal("0.00")
        component_lines = []
        
        for assignment in assignments:
            component = await self.component_def_repo.get_by_id(assignment.pay_component_id)
            if not component or not component.is_active:
                continue
            
            # Calculate amount
            if assignment.amount:
                amount = assignment.amount
            elif assignment.rate:
                # Rate-based calculation (e.g., percentage of base)
                base = await self._get_base_amount(employee_id, assignments)
                amount = base * (assignment.rate / Decimal("100"))
            else:
                amount = Decimal("0.00")
            
            component_lines.append({
                "component_code": component.component_code,
                "component_name": component.component_name,
                "component_type": component.component_type.value,
                "amount": amount
            })
            
            if component.component_type == ComponentType.EARNING:
                earnings += amount
            elif component.component_type == ComponentType.DEDUCTION:
                deductions += amount
            elif component.component_type == ComponentType.EMPLOYER_CONTRIBUTION:
                employer_contrib += amount
        
        # Add commissions
        unpaid_commissions = await self.commission_ledger_repo.list_unpaid_by_employee(employee_id)
        for commission in unpaid_commissions:
            if (commission.period_start <= pay_period_end and 
                commission.period_end >= pay_period_start):
                earnings += commission.total_commission
                component_lines.append({
                    "component_code": "COMMISSION",
                    "component_name": "Commission",
                    "component_type": ComponentType.EARNING.value,
                    "amount": commission.total_commission
                })
        
        # Add bonuses
        unpaid_bonuses = await self.bonus_repo.list_unpaid_by_employee(employee_id)
        for bonus in unpaid_bonuses:
            if bonus.bonus_date >= pay_period_start and bonus.bonus_date <= pay_period_end:
                earnings += bonus.bonus_amount
                component_lines.append({
                    "component_code": "BONUS",
                    "component_name": "Bonus",
                    "component_type": ComponentType.EARNING.value,
                    "amount": bonus.bonus_amount
                })
        
        net_pay = earnings - deductions
        
        return {
            "employee_id": employee_id,
            "gross_pay": earnings,
            "total_deductions": deductions,
            "net_pay": net_pay,
            "employer_contributions": employer_contrib,
            "currency": employee.currency,
            "component_lines": component_lines
        }
    
    async def _get_base_amount(
        self,
        employee_id: UUID,
        assignments: List
    ) -> Decimal:
        """Get base amount for rate calculations"""
        # Find BASIC component
        for assignment in assignments:
            component = await self.component_def_repo.get_by_id(assignment.pay_component_id)
            if component and component.component_code == "BASIC":
                return assignment.amount or Decimal("0.00")
        return Decimal("0.00")
