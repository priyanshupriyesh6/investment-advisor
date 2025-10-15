import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class InvestmentAdvisor:
    def __init__(self):
        self.risk_profiles = {
            'conservative': {'stocks': 0.2, 'bonds': 0.6, 'cash': 0.2},
            'moderate': {'stocks': 0.5, 'bonds': 0.4, 'cash': 0.1},
            'aggressive': {'stocks': 0.8, 'bonds': 0.15, 'cash': 0.05}
        }
        self.usd_to_inr_rate = self.get_usd_inr_rate()
        
        # Indian Market Instruments
        self.indian_stocks = {
            'large_cap': [
                {'symbol': 'RELIANCE.NS', 'name': 'Reliance Industries'},
                {'symbol': 'TCS.NS', 'name': 'Tata Consultancy Services'},
                {'symbol': 'HDFCBANK.NS', 'name': 'HDFC Bank'},
                {'symbol': 'INFY.NS', 'name': 'Infosys'},
                {'symbol': 'ICICIBANK.NS', 'name': 'ICICI Bank'}
            ],
            'mid_cap': [
                {'symbol': 'GODREJPROP.NS', 'name': 'Godrej Properties'},
                {'symbol': 'TATAELXSI.NS', 'name': 'Tata Elxsi'},
                {'symbol': 'MPHASIS.NS', 'name': 'Mphasis'}
            ]
        }
        
        self.mutual_funds = {
            'equity': [
                {'code': 'INF179K01BE2', 'name': 'Axis Bluechip Fund Direct Growth', 'risk': 'moderate'},
                {'code': 'INF090I01LD9', 'name': 'ICICI Prudential Bluechip Fund Direct Plan Growth', 'risk': 'moderate'},
                {'code': 'INF209K01BR9', 'name': 'Mirae Asset Large Cap Fund Direct Plan Growth', 'risk': 'moderate'}
            ],
            'debt': [
                {'code': 'INF209K01NS1', 'name': 'Mirae Asset Short Term Fund Direct Growth', 'risk': 'conservative'},
                {'code': 'INF090I01XG8', 'name': 'ICICI Prudential Corporate Bond Fund Direct Plan Growth', 'risk': 'conservative'}
            ],
            'hybrid': [
                {'code': 'INF846K01940', 'name': 'DSP Equity & Bond Fund Direct Plan Growth', 'risk': 'moderate'},
                {'code': 'INF179K01CH2', 'name': 'Axis Triple Advantage Fund Direct Growth', 'risk': 'aggressive'}
            ]
        }
        
        self.bonds = {
            'govt': [
                {'name': '7.37% GS 2028', 'yield': 7.37, 'maturity': 2028},
                {'name': '7.26% GS 2029', 'yield': 7.26, 'maturity': 2029},
                {'name': '6.79% GS 2027', 'yield': 6.79, 'maturity': 2027}
            ],
            'corporate': [
                {'name': 'HDFC 7.95% 2025', 'yield': 7.95, 'maturity': 2025},
                {'name': 'LIC Housing 7.85% 2026', 'yield': 7.85, 'maturity': 2026}
            ]
        }

    def get_usd_inr_rate(self):
        """Fetch current USD to INR exchange rate"""
        try:
            inr = yf.Ticker("INR=X")
            return inr.history(period='1d')['Close'].iloc[-1]
        except:
            return 83.0  # Default approximate rate

    def get_indian_market_data(self, symbols):
        """Fetch current market data for Indian stocks"""
        data = {}
        for symbol in symbols:
            try:
                stock = yf.Ticker(symbol)
                current_data = stock.history(period='1d')
                if not current_data.empty:
                    data[symbol] = {
                        'price': current_data['Close'].iloc[-1],
                        'volume': current_data['Volume'].iloc[-1]
                    }
            except Exception as e:
                print(f"Error fetching data for {symbol}: {str(e)}")
        return data

    def calculate_investment_returns(self, amount, time_period, investment_type, monthly_increment=0):
        """Calculate expected returns based on investment type and parameters"""
        annual_return_rates = {
            'stocks': 0.10,  # 10% average annual return
            'bonds': 0.05,   # 5% average annual return
            'cash': 0.02     # 2% average annual return
        }

        if investment_type == 'fixed':
            # One-time investment
            total_amount = amount
            for asset, rate in annual_return_rates.items():
                yearly_return = amount * rate
                total_amount += yearly_return * time_period
            return total_amount

        elif investment_type == 'floating':
            # Investment with percentage increment
            total_amount = amount
            current_monthly = amount / 12  # Initial monthly investment
            for year in range(time_period):
                for month in range(12):
                    total_amount += current_monthly
                    # Apply returns monthly
                    for asset, rate in annual_return_rates.items():
                        monthly_return = total_amount * (rate / 12)
                        total_amount += monthly_return
                current_monthly *= (1 + monthly_increment)  # Increase monthly investment
            return total_amount

        elif investment_type == 'fixed-float':
            # Fixed monthly investment
            total_amount = amount
            monthly_amount = amount / 12
            for year in range(time_period):
                for month in range(12):
                    total_amount += monthly_amount
                    # Apply returns monthly
                    for asset, rate in annual_return_rates.items():
                        monthly_return = total_amount * (rate / 12)
                        total_amount += monthly_return
            return total_amount

    def get_investment_advice(self, amount, time_period, investment_type, risk_tolerance='moderate', monthly_increment=0):
        """Generate investment advice based on user inputs"""
        # Calculate expected returns
        expected_return = self.calculate_investment_returns(
            amount, time_period, investment_type, monthly_increment
        )

        # Get asset allocation based on risk profile
        allocation = self.risk_profiles[risk_tolerance]
        
        # Get Indian market recommendations
        stock_recommendations = []
        mf_recommendations = []
        bond_recommendations = []
        
        # Stock recommendations based on risk profile
        if risk_tolerance == 'conservative':
            stock_symbols = [stock['symbol'] for stock in self.indian_stocks['large_cap'][:2]]
        elif risk_tolerance == 'moderate':
            stock_symbols = [stock['symbol'] for stock in self.indian_stocks['large_cap'][:3]]
            stock_symbols.extend([stock['symbol'] for stock in self.indian_stocks['mid_cap'][:1]])
        else:  # aggressive
            stock_symbols = [stock['symbol'] for stock in self.indian_stocks['large_cap'][:3]]
            stock_symbols.extend([stock['symbol'] for stock in self.indian_stocks['mid_cap'][:2]])
        
        # Fetch current market data for recommended stocks
        stock_data = self.get_indian_market_data(stock_symbols)
        
        # Select mutual funds based on risk profile
        if risk_tolerance == 'conservative':
            mf_recommendations.extend(self.mutual_funds['debt'][:2])
            mf_recommendations.extend(self.mutual_funds['hybrid'][:1])
        elif risk_tolerance == 'moderate':
            mf_recommendations.extend(self.mutual_funds['equity'][:2])
            mf_recommendations.extend(self.mutual_funds['debt'][:1])
            mf_recommendations.extend(self.mutual_funds['hybrid'][:1])
        else:  # aggressive
            mf_recommendations.extend(self.mutual_funds['equity'][:3])
            mf_recommendations.extend(self.mutual_funds['hybrid'][:1])
        
        # Select bonds based on risk profile
        if risk_tolerance == 'conservative':
            bond_recommendations.extend(self.bonds['govt'][:2])
            bond_recommendations.extend(self.bonds['corporate'][:1])
        elif risk_tolerance == 'moderate':
            bond_recommendations.extend(self.bonds['govt'][:1])
            bond_recommendations.extend(self.bonds['corporate'][:1])
        else:  # aggressive
            bond_recommendations.extend(self.bonds['corporate'][:1])

        # Generate specific investment recommendations
        recommendations = {
            'total_expected_value': expected_return,
            'asset_allocation': {
                'stocks': {
                    'percentage': allocation['stocks'],
                    'amount': amount * allocation['stocks'],
                    'recommendations': [
                        {
                            'name': next(stock['name'] for stock in self.indian_stocks['large_cap'] + self.indian_stocks['mid_cap'] 
                                       if stock['symbol'] == symbol),
                            'symbol': symbol,
                            'current_price': stock_data.get(symbol, {}).get('price', 0)
                        }
                        for symbol in stock_symbols
                    ]
                },
                'mutual_funds': {
                    'percentage': allocation['bonds'] * 0.6,  # 60% of bonds allocation to mutual funds
                    'amount': amount * allocation['bonds'] * 0.6,
                    'recommendations': mf_recommendations
                },
                'bonds': {
                    'percentage': allocation['bonds'] * 0.4,  # 40% of bonds allocation to direct bonds
                    'amount': amount * allocation['bonds'] * 0.4,
                    'recommendations': bond_recommendations
                },
                'cash': {
                    'percentage': allocation['cash'],
                    'amount': amount * allocation['cash'],
                    'recommendation': 'High-yield savings account or liquid funds'
                }
            },
            'investment_type': investment_type,
            'time_period': time_period,
            'risk_profile': risk_tolerance
        }
        
        return recommendations

    def explain_investment_strategy(self, advice, risk_tolerance):
        """Provide detailed explanation of the investment strategy"""
        strategy = {
            'overview': f"""
Investment Strategy Overview for {risk_tolerance.title()} Risk Profile:
------------------------------------------------------------""",
            
            'stocks': f"""
1. Stocks Strategy ({advice['asset_allocation']['stocks']['percentage']*100}% of portfolio - ₹{advice['asset_allocation']['stocks']['amount']:,.2f})
   - Large-cap Stocks (75% of stock allocation)
     * Focuses on established companies with strong market presence
     * Provides stability and reliable growth
     * Selected companies have proven track records and strong fundamentals
   - Mid-cap Stocks (25% of stock allocation)
     * Companies with high growth potential
     * Balanced mix of stability and growth opportunities
     * Carefully selected based on financial health and market position""",
            
            'mutual_funds': f"""
2. Mutual Funds Strategy ({advice['asset_allocation']['mutual_funds']['percentage']*100}% of portfolio - ₹{advice['asset_allocation']['mutual_funds']['amount']:,.2f})
   - Equity Mutual Funds (50% of MF allocation)
     * Professional management of your investments
     * Diversification across multiple sectors and companies
     * Focus on quality large-cap and mid-cap stocks
   - Debt Funds (25% of MF allocation)
     * Provides stability to the portfolio
     * Regular income through interest payments
     * Lower risk compared to equity funds
   - Hybrid Funds (25% of MF allocation)
     * Balanced exposure to both stocks and bonds
     * Automatic asset rebalancing by fund managers
     * Moderates overall portfolio risk""",
            
            'bonds': f"""
3. Bonds Strategy ({advice['asset_allocation']['bonds']['percentage']*100}% of portfolio - ₹{advice['asset_allocation']['bonds']['amount']:,.2f})
   - Government Bonds (60% of bond allocation)
     * Highest safety with sovereign guarantee
     * Regular interest payments
     * Helps preserve capital
   - Corporate Bonds (40% of bond allocation)
     * Higher yields than government bonds
     * Selected from highly-rated companies
     * Additional return with managed risk""",
            
            'cash': f"""
4. Cash/Liquid Funds ({advice['asset_allocation']['cash']['percentage']*100}% of portfolio - ₹{advice['asset_allocation']['cash']['amount']:,.2f})
   - Serves multiple purposes:
     * Emergency fund for unexpected needs
     * Ready capital for investment opportunities
     * Buffer for monthly incremental investments
   - Recommended instruments:
     * High-yield savings accounts
     * Liquid mutual funds
     * Short-term money market instruments""",
            
            'risk_management': """
5. Risk Management Strategy
   - Diversification across:
     * Multiple asset classes
     * Various market capitalizations
     * Different sectors and industries
     * Multiple investment styles
   - Regular portfolio rebalancing
   - Professional management through mutual funds
   - Mix of growth and value investments""",
            
            'monitoring': """
6. Portfolio Monitoring and Rebalancing
   - Quarterly portfolio review recommended
   - Rebalance when allocations deviate by >5%
   - Track performance against benchmarks
   - Adjust strategy based on:
     * Market conditions
     * Change in risk tolerance
     * Life goals and time horizon
     * Economic factors"""
        }
        
        return strategy