import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_superstore_sales_dataset() -> pd.DataFrame:
    """Enterprise E-commerce & Retail Superstore Sales Dataset."""
    np.random.seed(42)
    n = 650
    
    categories = {
        'Technology': ['Phones', 'Laptops', 'Accessories', 'Copiers'],
        'Furniture': ['Chairs', 'Tables', 'Bookcases', 'Furnishings'],
        'Office Supplies': ['Paper', 'Binders', 'Storage', 'Appliances', 'Art']
    }
    
    cat_keys = list(categories.keys())
    selected_cats = np.random.choice(cat_keys, size=n, p=[0.35, 0.30, 0.35])
    selected_subcats = [np.random.choice(categories[c]) for c in selected_cats]
    
    regions = ['North America', 'Europe', 'Asia Pacific', 'Latin America', 'Middle East']
    segments = ['Consumer', 'Corporate', 'Home Office']
    ship_modes = ['Standard Class', 'Second Class', 'First Class', 'Same Day']
    
    start_date = datetime(2023, 1, 1)
    dates = [start_date + timedelta(days=int(d)) for d in np.random.uniform(0, 720, n)]
    
    quantities = np.random.randint(1, 15, size=n)
    
    # Base prices by category
    base_prices = {
        'Phones': 350, 'Laptops': 950, 'Accessories': 45, 'Copiers': 1200,
        'Chairs': 180, 'Tables': 320, 'Bookcases': 150, 'Furnishings': 60,
        'Paper': 25, 'Binders': 15, 'Storage': 110, 'Appliances': 220, 'Art': 30
    }
    
    unit_prices = [base_prices.get(sc, 100) * np.random.uniform(0.85, 1.25) for sc in selected_subcats]
    sales = [round(q * p, 2) for q, p in zip(quantities, unit_prices)]
    discounts = np.random.choice([0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5], size=n, p=[0.4, 0.15, 0.15, 0.1, 0.1, 0.05, 0.05])
    
    # Profit margins
    margins = {
        'Technology': 0.28,
        'Furniture': 0.08,
        'Office Supplies': 0.22
    }
    profits = [
        round((s * (1 - d) * margins[c]) - (s * d * 0.5) + np.random.normal(0, 15), 2)
        for s, d, c in zip(sales, discounts, selected_cats)
    ]
    
    shipping_costs = [round(s * 0.06 + np.random.uniform(5, 25), 2) for s in sales]
    satisfaction_scores = np.random.choice([1, 2, 3, 4, 5], size=n, p=[0.05, 0.08, 0.17, 0.45, 0.25])
    
    df = pd.DataFrame({
        'Order_ID': [f'ORD-{2023000 + i}' for i in range(n)],
        'Order_Date': [d.strftime('%Y-%m-%d') for d in dates],
        'Region': np.random.choice(regions, size=n, p=[0.35, 0.25, 0.20, 0.12, 0.08]),
        'Customer_Segment': np.random.choice(segments, size=n, p=[0.50, 0.30, 0.20]),
        'Category': selected_cats,
        'Sub_Category': selected_subcats,
        'Ship_Mode': np.random.choice(ship_modes, size=n, p=[0.55, 0.20, 0.18, 0.07]),
        'Sales': sales,
        'Quantity': quantities,
        'Discount': discounts,
        'Profit': profits,
        'Shipping_Cost': shipping_costs,
        'Customer_Rating': satisfaction_scores
    })
    
    # Inject a few realistic missing values and outlier for cleaning demonstration
    df.loc[np.random.choice(df.index, size=14, replace=False), 'Customer_Rating'] = np.nan
    df.loc[np.random.choice(df.index, size=8, replace=False), 'Shipping_Cost'] = np.nan
    df.loc[df.index[12], 'Sales'] = 28500.0  # High outlier
    df.loc[df.index[45], 'Profit'] = -4200.0  # Negative outlier
    
    return df

def get_telecom_churn_dataset() -> pd.DataFrame:
    """Telecom Customer Churn & Retention Analytics Dataset."""
    np.random.seed(101)
    n = 600
    
    tenures = np.random.randint(1, 72, size=n)
    contracts = np.random.choice(['Month-to-month', 'One year', 'Two year'], size=n, p=[0.55, 0.25, 0.20])
    internet_types = np.random.choice(['Fiber optic', 'DSL', 'No'], size=n, p=[0.45, 0.35, 0.20])
    payment_methods = ['Electronic check', 'Mailed check', 'Bank transfer', 'Credit card']
    
    monthly_charges = []
    for it, c in zip(internet_types, contracts):
        base = 25 if it == 'No' else (75 if it == 'Fiber optic' else 50)
        discount = 10 if c == 'Two year' else (5 if c == 'One year' else 0)
        monthly_charges.append(round(base - discount + np.random.normal(0, 8), 2))
    
    total_charges = [round(mc * t + np.random.uniform(0, 50), 2) for mc, t in zip(monthly_charges, tenures)]
    support_tickets = np.random.poisson(lam=1.6, size=n)
    
    # Churn probability based on contract, internet type, monthly charge and support tickets
    churn_list = []
    for c, it, mc, st in zip(contracts, internet_types, monthly_charges, support_tickets):
        prob = 0.15
        if c == 'Month-to-month':
            prob += 0.25
        if it == 'Fiber optic':
            prob += 0.12
        if st >= 3:
            prob += 0.28
        if mc > 80:
            prob += 0.10
        prob = min(0.92, max(0.04, prob))
        churn_list.append('Yes' if np.random.rand() < prob else 'No')
        
    df = pd.DataFrame({
        'Customer_ID': [f'TELCO-{84920 + i}' for i in range(n)],
        'Gender': np.random.choice(['Male', 'Female'], size=n),
        'Senior_Citizen': np.random.choice([0, 1], size=n, p=[0.82, 0.18]),
        'Partner': np.random.choice(['Yes', 'No'], size=n, p=[0.48, 0.52]),
        'Tenure_Months': tenures,
        'Internet_Service': internet_types,
        'Contract': contracts,
        'Payment_Method': np.random.choice(payment_methods, size=n),
        'Monthly_Charges': monthly_charges,
        'Total_Charges': total_charges,
        'Support_Tickets': support_tickets,
        'Churn': churn_list
    })
    
    # Inject missing total charges for new customers (tenure = 1)
    df.loc[df['Tenure_Months'] == 1, 'Total_Charges'] = np.nan
    return df

def get_hr_analytics_dataset() -> pd.DataFrame:
    """HR Talent Management & Employee Attrition Dataset."""
    np.random.seed(88)
    n = 550
    
    departments = ['Engineering', 'Sales', 'Product', 'Marketing', 'Human Resources', 'Operations']
    roles = {
        'Engineering': ['Software Engineer', 'Senior Architect', 'QA Lead', 'DevOps Specialist'],
        'Sales': ['Account Executive', 'Sales Lead', 'BD Representative'],
        'Product': ['Product Manager', 'UX Designer', 'Data Analyst'],
        'Marketing': ['Content Strategist', 'Growth Marketer', 'Brand Manager'],
        'Human Resources': ['HR Generalist', 'Recruiting Partner'],
        'Operations': ['Operations Analyst', 'Supply Coordinator']
    }
    
    dep_list = np.random.choice(departments, size=n, p=[0.32, 0.25, 0.15, 0.12, 0.08, 0.08])
    role_list = [np.random.choice(roles[d]) for d in dep_list]
    ages = np.random.randint(22, 60, size=n)
    experience_years = [max(0, a - np.random.randint(20, 25)) for a in ages]
    tenure_years = [min(exp, np.random.randint(0, 16)) for exp in experience_years]
    
    base_salaries = {
        'Engineering': 95000, 'Sales': 78000, 'Product': 90000,
        'Marketing': 68000, 'Human Resources': 64000, 'Operations': 62000
    }
    
    monthly_incomes = [
        int((base_salaries[d] / 12) + (exp * 280) + np.random.normal(0, 450))
        for d, exp in zip(dep_list, experience_years)
    ]
    
    job_satisfactions = np.random.choice([1, 2, 3, 4], size=n, p=[0.12, 0.20, 0.40, 0.28])
    overtime = np.random.choice(['Yes', 'No'], size=n, p=[0.30, 0.70])
    performance_ratings = np.random.choice(['Meets Expectations', 'Exceeds Expectations', 'Needs Improvement'], size=n, p=[0.65, 0.25, 0.10])
    
    attrition = []
    for js, ot, pr, sal, ten in zip(job_satisfactions, overtime, performance_ratings, monthly_incomes, tenure_years):
        score = 0.10
        if js <= 2:
            score += 0.25
        if ot == 'Yes':
            score += 0.20
        if sal < 5000:
            score += 0.15
        if ten <= 1:
            score += 0.12
        attrition.append('Yes' if np.random.rand() < min(0.85, score) else 'No')
        
    return pd.DataFrame({
        'Employee_ID': [f'EMP-{5000 + i}' for i in range(n)],
        'Age': ages,
        'Department': dep_list,
        'Job_Role': role_list,
        'Total_Experience_Years': experience_years,
        'Tenure_At_Company': tenure_years,
        'Monthly_Income_USD': monthly_incomes,
        'Job_Satisfaction_1to4': job_satisfactions,
        'Overtime': overtime,
        'Performance_Rating': performance_ratings,
        'Work_Life_Balance': np.random.choice([1, 2, 3, 4], size=n, p=[0.10, 0.28, 0.44, 0.18]),
        'Attrition': attrition
    })

def get_fintech_transactions_dataset() -> pd.DataFrame:
    """FinTech Card Fraud & Transaction Risk Dataset."""
    np.random.seed(777)
    n = 600
    
    merchant_cats = ['Travel & Airlines', 'Electronics', 'Groceries', 'Dining & Restaurants', 'Fashion', 'Digital Entertainment', 'Crypto & Gaming']
    devices = ['iOS App', 'Android App', 'Web Browser', 'POS Terminal']
    card_types = ['Visa Infinite', 'Mastercard Platinum', 'Amex Gold', 'Standard Debit']
    
    amounts = np.random.exponential(scale=110, size=n) + 5
    amounts = [round(min(5000, a), 2) for a in amounts]
    
    is_foreign = np.random.choice(['Yes', 'No'], size=n, p=[0.15, 0.85])
    risk_scores = []
    is_fraud = []
    
    for a, f, mc in zip(amounts, is_foreign, np.random.choice(merchant_cats, size=n)):
        base_risk = int(np.random.beta(2, 6) * 100)
        if f == 'Yes':
            base_risk += 25
        if a > 800:
            base_risk += 30
        if mc in ['Crypto & Gaming', 'Electronics']:
            base_risk += 15
        risk_score = min(99, max(1, base_risk))
        risk_scores.append(risk_score)
        is_fraud.append('Fraud' if risk_score > 75 and np.random.rand() < 0.65 else 'Legitimate')
        
    return pd.DataFrame({
        'Transaction_ID': [f'TXN-{900000 + i}' for i in range(n)],
        'Timestamp': [(datetime(2024, 3, 1) + timedelta(hours=i * 3.5)).strftime('%Y-%m-%d %H:%M') for i in range(n)],
        'Merchant_Category': np.random.choice(merchant_cats, size=n),
        'Amount_USD': amounts,
        'Card_Type': np.random.choice(card_types, size=n),
        'Device_Channel': np.random.choice(devices, size=n),
        'Is_International': is_foreign,
        'Risk_Score': risk_scores,
        'Status': is_fraud
    })

def get_saas_metrics_dataset() -> pd.DataFrame:
    """SaaS Product Engagement & Monthly Recurring Revenue (MRR) Dataset."""
    np.random.seed(333)
    n = 500
    
    plans = ['Starter', 'Growth', 'Pro', 'Enterprise']
    plan_prices = {'Starter': 49, 'Growth': 199, 'Pro': 499, 'Enterprise': 1499}
    
    plan_choices = np.random.choice(plans, size=n, p=[0.40, 0.30, 0.20, 0.10])
    seat_counts = []
    mrrs = []
    
    for p in plan_choices:
        seats = np.random.randint(1, 5) if p == 'Starter' else (
            np.random.randint(5, 20) if p == 'Growth' else (
                np.random.randint(20, 100) if p == 'Pro' else np.random.randint(100, 1000)
            )
        )
        seat_counts.append(seats)
        mrr = plan_prices[p] + (seats * 12) + np.random.normal(0, 20)
        mrrs.append(round(max(49, mrr), 2))
        
    adoption_scores = [round(min(100, max(10, np.random.normal(68, 18))), 1) for _ in range(n)]
    storage_gb = [round(min(2000, max(1, s * np.random.uniform(2.5, 12.0))), 1) for s in seat_counts]
    nps_scores = np.random.choice([-100, 0, 50, 70, 90, 100], size=n, p=[0.05, 0.10, 0.20, 0.30, 0.25, 0.10])
    
    return pd.DataFrame({
        'Account_ID': [f'ACCT-{1000 + i}' for i in range(n)],
        'Plan_Tier': plan_choices,
        'Active_Users': seat_counts,
        'Monthly_Recurring_Revenue': mrrs,
        'Storage_Used_GB': storage_gb,
        'Feature_Adoption_Score': adoption_scores,
        'NPS_Score': nps_scores,
        'Region': np.random.choice(['US-East', 'US-West', 'EU-Central', 'AP-South'], size=n),
        'Support_Tier': np.random.choice(['Standard', 'Priority', 'Dedicated 24/7'], size=n, p=[0.6, 0.3, 0.1])
    })

DATASET_GENERATORS = {
    'superstore_sales': {
        'name': 'Superstore Sales & Profit',
        'category': 'E-Commerce & Retail',
        'description': '650 orders with Sales, Profit, Categories, Regions, and Customer Segments.',
        'fn': get_superstore_sales_dataset
    },
    'telecom_churn': {
        'name': 'Telecom Customer Churn',
        'category': 'Customer Retention',
        'description': '600 subscribers with monthly charges, contract types, support tickets & churn flags.',
        'fn': get_telecom_churn_dataset
    },
    'hr_analytics': {
        'name': 'HR Workforce & Attrition',
        'category': 'Human Resources',
        'description': '550 employees tracking satisfaction, salary, department, performance, and attrition.',
        'fn': get_hr_analytics_dataset
    },
    'fintech_transactions': {
        'name': 'FinTech Fraud & Risk',
        'category': 'Financial Services',
        'description': '600 credit transactions assessing risk scores, foreign purchases, and fraud status.',
        'fn': get_fintech_transactions_dataset
    },
    'saas_metrics': {
        'name': 'SaaS Product & MRR Metrics',
        'category': 'B2B Software',
        'description': '500 SaaS accounts analyzing plan tiers, MRR revenue, feature adoption, and storage.',
        'fn': get_saas_metrics_dataset
    }
}
