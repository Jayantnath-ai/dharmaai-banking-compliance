from faker import Faker
import json
import uuid
from random import gauss, choice

fake = Faker()

def gen_transaction():
    return {
        "tx_id": str(uuid.uuid4()),
        "timestamp": fake.iso8601(),
        "amount": round(abs(gauss(5000, 8000)), 2),
        "currency": "USD",
        "sender_account": fake.bban(),
        "receiver_account": fake.bban(),
        "sender_country": fake.country_code(),
        "receiver_country": fake.country_code(),
        "purpose_code": choice(["CASH", "PAYMENT", "TRANSFER"]),
        "customer_risk_score": choice([20, 40, 60, 80, 95])
    }

def gen_customer():
    return {
        "customer_id": str(uuid.uuid4()),
        "name": fake.name(),
        "dob": fake.date_of_birth(minimum_age=18, maximum_age=85).isoformat(),
        "country_of_residence": fake.country_code(),
        "risk_rating": choice(["Low","Medium","High"]),
        "kyc_completed": True,
        "kyc_date": fake.date_between(start_date='-2y', end_date='today').isoformat()
    }

if __name__ == "__main__":
    # generate 10k txs
    txs = [gen_transaction() for _ in range(10000)]
    custs = [gen_customer() for _ in range(1000)]
    with open("transactions.json","w") as f:
        json.dump(txs, f, indent=2)
    with open("customers.json","w") as f:
        json.dump(custs, f, indent=2)
    print("Mock data written to transactions.json and customers.json")
