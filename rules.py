from durable.lang import *

with ruleset('aml'):
    # Rule: flag transactions > $10,000
    @when_all(m.amount > 10000)
    def large_tx(c):
        print(f"ALERT: large txn {c.m.tx_id} amount={c.m.amount}")

# To test:
# from durable.engine import run_all
# import json
# txs = json.load(open("transactions.json"))
# for tx in txs:
#     post('aml', tx)
# run_all()
