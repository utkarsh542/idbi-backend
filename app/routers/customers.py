from fastapi import APIRouter, HTTPException
from app.services.customer_service import load_customers, get_customer, calculate_metrics

router = APIRouter(prefix="/api/customers", tags=["customers"])

@router.get("")
def list_customers():
    customers = load_customers()
    # Return brief info for the picker list
    return [
        {
            "id": c["id"],
            "name": c["name"],
            "city": c["city"],
            "occupation": c["occupation"],
            "risk_profile": c["risk_profile"],
            "portfolio_value": c["portfolio_value"]
        } for c in customers
    ]

@router.get("/{customer_id}")
def get_customer_details(customer_id: str):
    customer = get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer

@router.get("/{customer_id}/metrics")
def get_customer_metrics(customer_id: str):
    customer = get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return calculate_metrics(customer)
