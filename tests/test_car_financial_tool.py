#!/usr/bin/env python3
"""
Unit tests for CarFinancialTool.
"""

import unittest
import math
from decimal import Decimal
from tools.car_financial_tool import CarFinancialTool, CarFinancialError


class TestCarFinancialTool(unittest.TestCase):
    """Test cases for CarFinancialTool."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool = CarFinancialTool()

    def test_calculate_monthly_payment_basic(self):
        """Test basic monthly payment calculation."""
        # Test case: $100,000 loan, 10% annual rate, 3 years
        principal = 100000
        annual_rate = 0.10
        years = 3
        
        monthly_payment = self.tool.calculate_monthly_payment(principal, annual_rate, years)
        
        # Expected monthly payment should be around $3,227.50
        # (calculated using standard loan formula)
        expected_payment = 3227.50
        self.assertAlmostEqual(monthly_payment, expected_payment, delta=50)

    def test_calculate_monthly_payment_zero_interest(self):
        """Test monthly payment calculation with zero interest rate."""
        principal = 100000
        annual_rate = 0.0
        years = 3
        
        monthly_payment = self.tool.calculate_monthly_payment(principal, annual_rate, years)
        expected_payment = principal / (years * 12)  # 100000 / 36 = 2777.78
        
        self.assertAlmostEqual(monthly_payment, expected_payment, places=2)

    def test_calculate_monthly_payment_high_interest(self):
        """Test monthly payment calculation with high interest rate."""
        principal = 50000
        annual_rate = 0.20  # 20% annual rate
        years = 4
        
        monthly_payment = self.tool.calculate_monthly_payment(principal, annual_rate, years)
        
        # With 20% annual rate, monthly payment should be higher
        self.assertGreater(monthly_payment, 1500)  # Should be significantly higher than zero interest

    def test_financing_plan_basic_scenario(self):
        """Test basic financing plan calculation."""
        args = {
            "car_price": 300000,
            "down_payment": 60000,
            "financing_years": 4
        }
        
        result = self.tool.execute(args, "test_user")
        
        # Should not contain error message
        self.assertNotIn("❌ Error", result)
        
        # Should contain expected sections
        self.assertIn("PLAN DE FINANCIAMIENTO AUTOMOTRIZ", result)
        self.assertIn("Precio del auto: $300,000.00", result)
        self.assertIn("Entrega: $60,000.00", result)
        self.assertIn("Monto a financiar: $240,000.00", result)
        self.assertIn("Tasa de interés anual: 10.0%", result)
        self.assertIn("Plazo: 4 años", result)

    def test_financing_plan_high_value_car(self):
        """Test financing plan for high-value car."""
        args = {
            "car_price": 800000,
            "down_payment": 200000,
            "financing_years": 5
        }
        
        result = self.tool.execute(args, "test_user")
        
        self.assertNotIn("❌ Error", result)
        self.assertIn("Precio del auto: $800,000.00", result)
        self.assertIn("Entrega: $200,000.00", result)
        self.assertIn("Monto a financiar: $600,000.00", result)

    def test_financing_plan_low_down_payment(self):
        """Test financing plan with low down payment (10% down)."""
        args = {
            "car_price": 400000,
            "down_payment": 40000,  # 10% down
            "financing_years": 6
        }
        
        result = self.tool.execute(args, "test_user")
        
        self.assertNotIn("❌ Error", result)
        self.assertIn("Monto a financiar: $360,000.00", result)
        self.assertIn("Plazo: 6 años", result)

    def test_financing_plan_high_down_payment(self):
        """Test financing plan with high down payment (50% down)."""
        args = {
            "car_price": 250000,
            "down_payment": 125000,  # 50% down
            "financing_years": 3
        }
        
        result = self.tool.execute(args, "test_user")
        
        self.assertNotIn("❌ Error", result)
        self.assertIn("Monto a financiar: $125,000.00", result)
        self.assertIn("Plazo: 3 años", result)

    def test_financing_plan_minimum_years(self):
        """Test financing plan with minimum years (3)."""
        args = {
            "car_price": 150000,
            "down_payment": 30000,
            "financing_years": 3
        }
        
        result = self.tool.execute(args, "test_user")
        
        self.assertNotIn("❌ Error", result)
        self.assertIn("Plazo: 3 años", result)

    def test_financing_plan_maximum_years(self):
        """Test financing plan with maximum years (6)."""
        args = {
            "car_price": 500000,
            "down_payment": 100000,
            "financing_years": 6
        }
        
        result = self.tool.execute(args, "test_user")
        
        self.assertNotIn("❌ Error", result)
        self.assertIn("Plazo: 6 años", result)

    def test_error_missing_parameters(self):
        """Test error handling for missing parameters."""
        # Missing car_price
        args = {
            "down_payment": 50000,
            "financing_years": 4
        }
        
        result = self.tool.execute(args, "test_user")
        self.assertIn(CarFinancialError.MISSING_PARAMS.value.split('(')[0], result)

        # Missing down_payment
        args = {
            "car_price": 200000,
            "financing_years": 4
        }
        
        result = self.tool.execute(args, "test_user")
        self.assertIn(CarFinancialError.MISSING_PARAMS.value.split('(')[0], result)

        # Missing financing_years
        args = {
            "car_price": 200000,
            "down_payment": 50000
        }
        
        result = self.tool.execute(args, "test_user")
        self.assertIn(CarFinancialError.MISSING_PARAMS.value.split('(')[0], result)

    def test_error_invalid_car_price(self):
        """Test error handling for invalid car price."""
        args = {
            "car_price": 0,
            "down_payment": 50000,
            "financing_years": 4
        }
        
        result = self.tool.execute(args, "test_user")
        self.assertIn("Error: El precio del auto debe ser mayor a 0", result)

        args = {
            "car_price": -1000,
            "down_payment": 50000,
            "financing_years": 4
        }
        
        result = self.tool.execute(args, "test_user")
        self.assertIn("Error: El precio del auto debe ser mayor a 0", result)

    def test_error_invalid_down_payment(self):
        """Test error handling for invalid down payment."""
        args = {
            "car_price": 200000,
            "down_payment": -1000,
            "financing_years": 4
        }
        
        result = self.tool.execute(args, "test_user")
        self.assertIn(CarFinancialError.INVALID_PRICE_OR_DOWN.value, result)

    def test_error_down_payment_greater_than_car_price(self):
        """Test error handling when down payment is greater than car price."""
        args = {
            "car_price": 200000,
            "down_payment": 250000,
            "financing_years": 4
        }
        
        result = self.tool.execute(args, "test_user")
        self.assertIn(CarFinancialError.DOWN_PAYMENT_TOO_HIGH.value, result)

        # Test equal case
        args = {
            "car_price": 200000,
            "down_payment": 200000,
            "financing_years": 4
        }
        
        result = self.tool.execute(args, "test_user")
        self.assertIn(CarFinancialError.DOWN_PAYMENT_TOO_HIGH.value, result)

    def test_error_invalid_financing_years(self):
        """Test error handling for invalid financing years."""
        # Too few years
        args = {
            "car_price": 200000,
            "down_payment": 50000,
            "financing_years": 2
        }
        
        result = self.tool.execute(args, "test_user")
        self.assertIn("Error: El plazo de financiamiento debe estar entre", result)

        # Too many years
        args = {
            "car_price": 200000,
            "down_payment": 50000,
            "financing_years": 7
        }
        
        result = self.tool.execute(args, "test_user")
        self.assertIn("Error: El plazo de financiamiento debe estar entre", result)

    def test_error_invalid_data_types(self):
        """Test error handling for invalid data types."""
        args = {
            "car_price": "invalid",
            "down_payment": 50000,
            "financing_years": 4
        }
        
        result = self.tool.execute(args, "test_user")
        self.assertIn(CarFinancialError.INVALID_VALUES.value, result)

        args = {
            "car_price": 200000,
            "down_payment": "invalid",
            "financing_years": 4
        }
        
        result = self.tool.execute(args, "test_user")
        self.assertIn(CarFinancialError.INVALID_VALUES.value, result)

        args = {
            "car_price": 200000,
            "down_payment": 50000,
            "financing_years": "invalid"
        }
        
        result = self.tool.execute(args, "test_user")
        self.assertIn(CarFinancialError.INVALID_VALUES.value, result)

    def test_financing_calculations_accuracy(self):
        """Test accuracy of financing calculations."""
        args = {
            "car_price": 100000,
            "down_payment": 20000,
            "financing_years": 3
        }
        
        result = self.tool.execute(args, "test_user")
        
        # Extract values from result for verification
        self.assertIn("Monto a financiar: $80,000.00", result)
        self.assertIn("Tasa de interés anual: 10.0%", result)
        self.assertIn("Plazo: 3 años (36 meses)", result)
        
        # Verify monthly payment calculation
        loan_amount = 80000
        monthly_rate = 0.10 / 12
        num_payments = 36
        
        expected_monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
        
        # The result should contain the calculated monthly payment
        self.assertIn(f"${expected_monthly_payment:,.2f}", result)

    def test_different_car_price_scenarios(self):
        """Test various car price scenarios."""
        scenarios = [
            {"car_price": 50000, "down_payment": 10000, "years": 3},   # Low-end car
            {"car_price": 150000, "down_payment": 30000, "years": 4},  # Mid-range car
            {"car_price": 300000, "down_payment": 60000, "years": 5},  # High-end car
            {"car_price": 600000, "down_payment": 120000, "years": 6}, # Luxury car
        ]
        
        for scenario in scenarios:
            args = {
                "car_price": scenario["car_price"],
                "down_payment": scenario["down_payment"],
                "financing_years": scenario["years"]
            }
            
            result = self.tool.execute(args, "test_user")
            self.assertNotIn("❌ Error", result)
            
            # Verify loan amount calculation
            expected_loan = scenario["car_price"] - scenario["down_payment"]
            self.assertIn(f"Monto a financiar: ${expected_loan:,.2f}", result)

    def test_different_down_payment_percentages(self):
        """Test various down payment percentages."""
        car_price = 200000
        scenarios = [
            {"down_payment": 20000, "percentage": "10%"},   # 10% down
            {"down_payment": 40000, "percentage": "20%"},   # 20% down
            {"down_payment": 60000, "percentage": "30%"},   # 30% down
            {"down_payment": 80000, "percentage": "40%"},   # 40% down
            {"down_payment": 100000, "percentage": "50%"},  # 50% down
        ]
        
        for scenario in scenarios:
            args = {
                "car_price": car_price,
                "down_payment": scenario["down_payment"],
                "financing_years": 4
            }
            
            result = self.tool.execute(args, "test_user")
            self.assertNotIn("❌ Error", result)
            
            # Verify down payment and loan amount
            self.assertIn(f"Entrega: ${scenario['down_payment']:,.2f}", result)
            expected_loan = car_price - scenario["down_payment"]
            self.assertIn(f"Monto a financiar: ${expected_loan:,.2f}", result)

    def test_monthly_payment_comparison(self):
        """Test that longer terms result in lower monthly payments."""
        car_price = 250000
        down_payment = 50000
        loan_amount = car_price - down_payment
        
        # Calculate monthly payments for different terms
        payment_3_years = self.tool.calculate_monthly_payment(loan_amount, 0.10, 3)
        payment_4_years = self.tool.calculate_monthly_payment(loan_amount, 0.10, 4)
        payment_5_years = self.tool.calculate_monthly_payment(loan_amount, 0.10, 5)
        payment_6_years = self.tool.calculate_monthly_payment(loan_amount, 0.10, 6)
        
        # Longer terms should have lower monthly payments
        self.assertGreater(payment_3_years, payment_4_years)
        self.assertGreater(payment_4_years, payment_5_years)
        self.assertGreater(payment_5_years, payment_6_years)

    def test_total_interest_calculation(self):
        """Test that total interest increases with longer terms."""
        car_price = 300000
        down_payment = 60000
        loan_amount = car_price - down_payment
        
        # Calculate total payments for different terms
        def get_total_payments(years):
            monthly_payment = self.tool.calculate_monthly_payment(loan_amount, 0.10, years)
            return monthly_payment * years * 12
        
        total_3_years = get_total_payments(3)
        total_4_years = get_total_payments(4)
        total_5_years = get_total_payments(5)
        total_6_years = get_total_payments(6)
        
        # Longer terms should have higher total payments (more interest)
        self.assertLess(total_3_years, total_4_years)
        self.assertLess(total_4_years, total_5_years)
        self.assertLess(total_5_years, total_6_years)

    def test_tool_definition(self):
        """Test that tool definition is properly formatted."""
        tool_def = self.tool.get_tool_definition()
        
        self.assertIn("type", tool_def)
        self.assertEqual(tool_def["type"], "function")
        
        self.assertIn("function", tool_def)
        function_def = tool_def["function"]
        
        self.assertIn("name", function_def)
        self.assertEqual(function_def["name"], "calculate_car_financing")
        
        self.assertIn("description", function_def)
        self.assertIn("parameters", function_def)
        
        # Check required parameters
        params = function_def["parameters"]
        self.assertIn("properties", params)
        self.assertIn("required", params)
        
        required_params = params["required"]
        self.assertIn("car_price", required_params)
        self.assertIn("down_payment", required_params)
        self.assertIn("financing_years", required_params)

    def test_general_exception_handling(self):
        """Test that general exceptions are handled gracefully."""
        # Mock a scenario that would cause a general exception
        # by passing None values that would cause issues in calculations
        args = {
            "car_price": None,
            "down_payment": None,
            "financing_years": None
        }
        
        result = self.tool.execute(args, "test_user")
        
        # Should return an error message
        self.assertIn("Error", result)


if __name__ == "__main__":
    unittest.main() 