"""
Tool for calculating car financing plans.
"""

from typing import Dict, Any, Optional
from enum import Enum

class CarFinancialError(str, Enum):
    MISSING_PARAMS = "Error: Todos los parámetros son requeridos (precio del auto, enganche, años de financiamiento)"
    INVALID_VALUES = "Error: Los valores deben ser números válidos"
    INVALID_PRICE_OR_DOWN = "Error: El precio del auto debe ser mayor a 0 y el enganche no puede ser negativo"
    DOWN_PAYMENT_TOO_HIGH = "Error: El enganche no puede ser mayor o igual al precio del auto"
    INVALID_YEARS = "Error: El plazo de financiamiento debe estar entre {min_years} y {max_years} años"

class CarFinancialTool:
    def __init__(self):
        """Initialize the tool."""
        self.annual_interest_rate = 0.10  # 10% annual interest rate
        self.min_years = 3
        self.max_years = 6

    def get_tool_definition(self) -> Dict[str, Any]:
        """
        Get the tool definition for OpenAI API.

        Returns:
            Dict containing tool definition
        """
        return {
            "type": "function",
            "function": {
                "name": "calculate_car_financing",
                "description": (
                    "Calcula un plan de financiamiento para la compra de un auto. "
                    "Utiliza una tasa de interés anual fija del 10%. "
                    "Es útil cuando el usuario pregunta sobre pagos mensuales, financiamiento o hipotecas para un auto."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "car_price": {
                            "type": "number",
                            "description": "Precio total del auto en pesos"
                        },
                        "down_payment": {
                            "type": "number",
                            "description": "Enganche o pago inicial en pesos"
                        },
                        "financing_years": {
                            "type": "integer",
                            "description": "Plazo de financiamiento en años (entre 3 y 6 años)",
                            "minimum": 3,
                            "maximum": 6
                        }
                    },
                    "required": ["car_price", "down_payment", "financing_years"]
                }
            }
        }

    def calculate_monthly_payment(self, principal: float, annual_rate: float, years: int) -> float:
        """
        Calculate monthly payment using the standard loan formula.

        Args:
            principal: Loan amount
            annual_rate: Annual interest rate (as decimal)
            years: Loan term in years

        Returns:
            Monthly payment amount
        """
        monthly_rate = annual_rate / 12
        num_payments = years * 12

        if monthly_rate == 0:
            return principal / num_payments

        # Standard loan payment formula
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
        return monthly_payment

    def execute(self, args: Dict[str, Any], user_id: str) -> str:
        """
        Execute the tool.

        Args:
            args: Tool arguments containing car_price, down_payment, and financing_years
            user_id: User ID (not used in this tool)

        Returns:
            str: Formatted financing plan
        """
        try:
            car_price = args.get("car_price")
            down_payment = args.get("down_payment")
            financing_years = args.get("financing_years")

            if not all([car_price is not None, down_payment is not None, financing_years is not None]):
                return CarFinancialError.MISSING_PARAMS.value

            # Type conversion and validation
            try:
                car_price = float(car_price)  # type: ignore
                down_payment = float(down_payment)  # type: ignore
                financing_years = int(financing_years)  # type: ignore
            except (ValueError, TypeError):
                return CarFinancialError.INVALID_VALUES.value

            if car_price <= 0 or down_payment < 0:
                return CarFinancialError.INVALID_PRICE_OR_DOWN.value

            if down_payment >= car_price:
                return CarFinancialError.DOWN_PAYMENT_TOO_HIGH.value

            if financing_years < self.min_years or financing_years > self.max_years:
                return CarFinancialError.INVALID_YEARS.value.format(min_years=self.min_years, max_years=self.max_years)

            # Calculate financing details
            loan_amount = car_price - down_payment
            monthly_payment = self.calculate_monthly_payment(loan_amount, self.annual_interest_rate, financing_years)
            total_payments = monthly_payment * financing_years * 12
            total_interest = total_payments - loan_amount

            # Format the response
            response = f"""
                🚗 **PLAN DE FINANCIAMIENTO AUTOMOTRIZ de Kavak**
                
                📊 **Detalles del Auto:**
                • Precio del auto: ${car_price:,.2f} MXN
                • Entrega: ${down_payment:,.2f} MXN
                • Monto a financiar: ${loan_amount:,.2f} MXN
                
                💰 **Condiciones del Financiamiento:**
                • Tasa de interés anual: {self.annual_interest_rate * 100}%
                • Plazo: {financing_years} años ({financing_years * 12} meses)
                
                📈 **Pagos:**
                • Pago mensual: ${monthly_payment:,.2f} MXN
                • Total de pagos: ${total_payments:,.2f} MXN
                • Total de intereses: ${total_interest:,.2f} MXN
                
                💡 **Resumen:**
                • Pagarás ${total_payments:,.2f} MXN en total
                • Los intereses representan ${total_interest:,.2f} MXN adicionales
                • Tu pago mensual será de ${monthly_payment:,.2f} MXN
            """

            return response

        except Exception as e:
            return f"Error al calcular el financiamiento: {e}"