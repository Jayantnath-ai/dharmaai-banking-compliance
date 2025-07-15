# generators.py - Mock Data factory, parameterized by count
import uuid
from faker import Faker
from random import gauss, choice

fake = Faker()

def gen_customer():
    return {
        "customer_id":   str(uuid.uuid4()),
        "risk_rating":   choice(["Low", "Medium", "High"]),
        "kyc_completed": choice([True, False])
    }

def build_customer_map(num=200):
    customers = [gen_customer() for _ in range(num)]
    return {c["customer_id"]: c for c in customers}

def gen_transaction(customer_map):
    cid  = choice(list(customer_map.keys()))
    cust = customer_map[cid]
    return {
        "tx_id":           str(uuid.uuid4()),
        "timestamp":       fake.iso8601(),
        "amount":          round(abs(gauss(5000, 8000)), 2),
        "currency":        "USD",
        "sender_account":  fake.bban(),
        "receiver_account": fake.bban(),
        "sender_country":  fake.country_code(),
        "receiver_country": fake.country_code(),
        "purpose_code":    choice(["CASH", "PAYMENT", "TRANSFER"]),
        "customer_id":     cid,
        "risk_rating":     cust["risk_rating"],
        "kyc_completed":   cust["kyc_completed"],
        # GDPR & SOX fields
        "retention_period": choice([1, 3, 5, 7, 10]),
        "initiator_id":     fake.bothify("EMP-####"),
        "approver_id":      fake.bothify("EMP-####")
    }
