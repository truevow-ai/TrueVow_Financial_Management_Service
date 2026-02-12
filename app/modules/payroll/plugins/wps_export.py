"""WPS Export Plugin - UAE Wage Protection System"""
from abc import ABC, abstractmethod
from typing import List, Dict
from uuid import UUID
from datetime import date
from decimal import Decimal


class WPSExporter(ABC):
    """Abstract WPS exporter interface"""
    
    @abstractmethod
    def generate_sif_file(
        self,
        payroll_run_id: UUID,
        employees: List[Dict],
        pay_date: date
    ) -> bytes:
        """Generate WPS SIF file
        
        Args:
            payroll_run_id: Payroll run ID
            employees: List of employee payment data
            pay_date: Payment date
            
        Returns:
            SIF file content as bytes
        """
        pass
    
    @abstractmethod
    def validate_employee_data(self, employee_data: Dict) -> tuple[bool, str]:
        """Validate employee data for WPS
        
        Returns:
            (is_valid, error_message)
        """
        pass


class UAEWPSExporter(WPSExporter):
    """UAE WPS SIF file exporter"""
    
    def generate_sif_file(
        self,
        payroll_run_id: UUID,
        employees: List[Dict],
        pay_date: date
    ) -> bytes:
        """Generate WPS SIF file format"""
        lines = []
        
        # Header line
        lines.append("H|WPS|1.0")
        
        # Employee lines
        for emp in employees:
            # Format: E|LABOUR_ID|MOL_ID|IBAN|AMOUNT|CURRENCY|REFERENCE
            line = f"E|{emp['labour_id']}|{emp['mol_id']}|{emp['iban']}|{emp['net_pay']:.2f}|{emp['currency']}|{emp['reference']}"
            lines.append(line)
        
        # Footer line
        lines.append("F|END")
        
        return "\n".join(lines).encode("utf-8")
    
    def validate_employee_data(self, employee_data: Dict) -> tuple[bool, str]:
        """Validate employee data for WPS"""
        required_fields = ["labour_id", "mol_id", "iban", "net_pay", "currency"]
        
        for field in required_fields:
            if field not in employee_data or not employee_data[field]:
                return False, f"Missing required field: {field}"
        
        # Validate IBAN format (simplified)
        iban = employee_data["iban"]
        if not iban.startswith("AE"):
            return False, "IBAN must start with AE for UAE"
        
        if len(iban) < 23:
            return False, "IBAN must be at least 23 characters"
        
        # Validate amount
        if employee_data["net_pay"] <= 0:
            return False, "Net pay must be positive"
        
        return True, ""
