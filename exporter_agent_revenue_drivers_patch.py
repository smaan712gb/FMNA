
    # Add this method to EnhancedExporterAgent class
    
    def _calculate_revenue_drivers(self, financial_data: Dict, market_data: Dict, 
                                   company_name: str = "") -> Dict[str, float]:
        """
        Calculate revenue drivers from available financial data
        Uses industry heuristics when direct data not available
        """
        from fix_revenue_drivers_and_scenarios import RevenueDriverCalculator
        calculator = RevenueDriverCalculator()
        return calculator.calculate_revenue_drivers(financial_data, market_data, company_name)
    
    # Update the _create_drivers_tab method to use calculated drivers
    def _create_drivers_tab(self, ws, drivers: Dict[str, Any]):
        """Create business drivers tab with CALCULATED revenue drivers"""
        ws['A1'] = "KEY BUSINESS DRIVERS"
        ws['A1'].font = Font(size=14, bold=True)
        
        row = 3
        
        # Revenue drivers - NOW CALCULATED, NOT PLACEHOLDER
        ws[f'A{row}'] = "REVENUE DRIVERS"
        ws[f'A{row}'].font = Font(bold=True)
        ws[f'A{row}'].fill = PatternFill(start_color=IB_COLORS.LIGHT_BLUE,
                                         end_color=IB_COLORS.LIGHT_BLUE,
                                         fill_type="solid")
        row += 1
        
        revenue_drivers = {
            'Units Sold (M)': drivers.get('units_sold', 0),
            'Average Selling Price': drivers.get('avg_price', 0),
            'Customer Count (M)': drivers.get('customers', 0),
            'Revenue per Customer': drivers.get('revenue_per_customer', 0),
            'Market Share (%)': drivers.get('market_share', 0),
        }
        
        for key, value in revenue_drivers.items():
            ws[f'A{row}'] = key
            ws[f'B{row}'] = value
            if '%' in key:
                ws[f'B{row}'].number_format = '0.00%'
            elif 'Price' in key or 'Revenue per' in key:
                ws[f'B{row}'].number_format = '$#,##0.00'
            else:
                ws[f'B{row}'].number_format = '#,##0.00'
            
            # Add note if value is estimated
            if value > 0:
                ws[f'C{row}'] = "Estimated*" if key != 'Market Share (%)' else "Industry data required"
                ws[f'C{row}'].font = Font(italic=True, size=9)
            
            row += 1
        
        # Add footnote
        if any(v > 0 for v in revenue_drivers.values()):
            row += 1
            ws[f'A{row}'] = "*Revenue drivers estimated using industry benchmarks and company financials"
            ws[f'A{row}'].font = Font(italic=True, size=8)
            ws.merge_cells(f'A{row}:C{row}')
    