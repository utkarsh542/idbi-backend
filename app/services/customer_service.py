import json
import os
from typing import Dict, List, Any

DATA_FILE = os.path.join(os.path.dirname(__file__), "../data/customers.json")

def load_customers() -> List[Dict[str, Any]]:
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def get_customer(customer_id: str) -> Dict[str, Any]:
    customers = load_customers()
    for c in customers:
        if c["id"] == customer_id:
            return c
    return None

def calculate_metrics(customer: Dict[str, Any]) -> Dict[str, Any]:
    metrics = {
        "monthly_income": customer.get("monthly_income", 0),
        "monthly_expenses": customer.get("monthly_expenses", {}),
        "portfolio_value": customer.get("portfolio_value", 0),
        "spending_trend_6m": customer.get("spending_trend_6m", []),
        "asset_allocation": {"mutual_fund": 0, "sip": 0, "gold": 0, "etf": 0, "bond": 0, "equity": 0, "debt": 0, "other": 0},
        "holdings": customer.get("holdings", []),
        "goal_progress": [],
        "savings_rate": 0,
        "weighted_return": 0
    }

    # Calculate Savings Rate
    total_expenses = 0
    for k, v in metrics["monthly_expenses"].items():
        if isinstance(v, (int, float)):
            total_expenses += v
            
    if metrics["monthly_income"] > 0:
        savings = metrics["monthly_income"] - total_expenses
        metrics["savings_rate"] = round((savings / metrics["monthly_income"]) * 100, 1)

    # Calculate Asset Allocation & Weighted Return
    total_portfolio = 0
    weighted_returns = 0
    for h in metrics["holdings"]:
        val = h.get("value", 0)
        ret = h.get("returns", 0)
        h_type = h.get("type", "other")
        
        metrics["asset_allocation"][h_type] += val
        total_portfolio += val
        weighted_returns += (val * ret)

    if total_portfolio > 0:
        metrics["weighted_return"] = round(weighted_returns / total_portfolio, 2)
        # Convert absolute allocation to percentage
        for k in metrics["asset_allocation"]:
            metrics["asset_allocation"][k] = round((metrics["asset_allocation"][k] / total_portfolio) * 100, 1)

    # Calculate Goal Progress
    goals = customer.get("goals", [])
    for g in goals:
        target = g.get("target_amount", 0)
        current = g.get("current_amount", 0)
        progress_pct = round((current / target) * 100, 1) if target > 0 else 0
        
        goal_data = g.copy()
        goal_data["progress_pct"] = progress_pct
        metrics["goal_progress"].append(goal_data)

    return metrics
