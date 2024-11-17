from fastapi.encoders import jsonable_encoder
from openai import OpenAI
import os
import json

from models import *

def detect_duplicates(transactions: list[Transaction]) -> list[PossibleFraudInstance]:
    transaction_amounts = {transaction.amount for transaction in transactions}
    transactions_by_amount = {amount: [transaction for transaction in transactions if transaction.amount == amount] for amount in transaction_amounts}
    transactions_by_amount_filtered = [transaction_list for transaction_list in transactions_by_amount.values() if len(transaction_list) > 1]
    possible_fraud_instances: list[PossibleFraudInstance] = []

    for transaction_list in transactions_by_amount_filtered:
        while transaction_list:
            target_record = transaction_list.pop()
            for record in transaction_list:
                if record.memo == target_record.memo and record.payee == target_record.payee and record.description == target_record.description:
                    possible_fraud_instance = PossibleFraudInstance(
                        transactions = [target_record, record],
                        fraud_type = "duplicate"
                    )
                    possible_fraud_instances.append(possible_fraud_instance)
                    transaction_list.remove(record)
    return possible_fraud_instances

def detect_suspicious_payee(transactions: list[Transaction]) -> list[PossibleFraudInstance]:
    system_prompt = "You are a helpful AI data analyst, responsible for analyzing transaction records to find suspicious activity"
    user_prompt = f'''Based on the transaction data in JSON format that is below the line \"DATA BEGINS HERE\", determine whether any of these transactions appear to be suspicious. A transaction is suspicious if the transaction's memo, payee, or description fields appear to be vague, incoherent, are in a language other than English, or reference companies that could be based out of nations that are known to conduct financial fraud, such as China, Russia, or North Korea. Respond only with the transaction records of the suspicious transactions in JSON format. Do not explain why the transactions are suspicious, or provide any text output other than the transaction records. Do not wrap output in a markdown code block.
    The output of the data should be formatted as JSON serialized data following the below PossibleFraudInstance pydantic schema:

    class PossibleFraudInstance(BaseModel):
        transactions: list[Transaction]
        fraud_type: str # duplicate, suspicious_payee, large_p2p

    class Transaction(BaseModel):
        id: str
        posted: int
        amount: str
        description: str
        payee: str
        memo: str

    DATA BEGINS HERE
    {jsonable_encoder(transactions)}'''

    client = OpenAI(
        api_key=os.environ.get("LLM_API_KEY"),
        base_url=os.environ.get("LLM_BASE_URL")
    )

    responses = client.chat.completions.create(
        model='Meta-Llama-3.1-405B-Instruct',
        messages=[{"role": "system", "content": system_prompt}, {"role":"user", "content":user_prompt}]
    )

    received_transactions = json.loads(responses.choices[0].message.content)
    print(received_transactions)
    possible_fraud_instances = [PossibleFraudInstance(transactions=[transaction], fraud_type = "suspicious_payee") for transaction in received_transactions['transactions']]
    return possible_fraud_instances

def detect_large_p2p(transactions: list[Transaction]) -> list[PossibleFraudInstance]:
    threshold = 100
    p2p_services = ['venmo', 'zelle', 'cash app', 'paypal', 'apple cash']
    possible_fraud_instances: list[PossibleFraudInstance] = []
    for transaction in transactions:
        converted_transaction_amount = float(transaction.amount.replace("-", ""))
        amount_above_threshold = converted_transaction_amount >= threshold
        p2p_in_payee = any(p2p_service in transaction.payee.lower() for p2p_service in p2p_services)
        p2p_in_memo = any(p2p_service in transaction.memo.lower() for p2p_service in p2p_services)
        p2p_in_description = any(p2p_service in transaction.description.lower() for p2p_service in p2p_services)
        
        if amount_above_threshold and (p2p_in_payee or p2p_in_memo or p2p_in_description):
            possible_fraud_instance = PossibleFraudInstance(
                transactions = [transaction],
                fraud_type = "large_p2p"
            )
            possible_fraud_instances.append(possible_fraud_instance)

        return possible_fraud_instances



def detect_all(transactions: list[Transaction]) -> list[PossibleFraudInstance]:
    print()
    print(detect_duplicates(transactions))
    print()
    print(detect_suspicious_payee(transactions))
    print()
    print(detect_large_p2p(transactions))
    return detect_duplicates(transactions) + detect_suspicious_payee(transactions) + detect_large_p2p(transactions)