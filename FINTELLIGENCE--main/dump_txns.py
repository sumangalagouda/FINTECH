from app import create_app
from app.extensions import db
from app.models.transaction import Transaction

app = create_app()
with app.app_context():
    txns = Transaction.query.limit(20).all()
    for t in txns:
        print(f"ID: {t.id} | Type: {t.type} | Amt: {t.amount} | Sender: {t.sender_account} | Receiver: {t.receiver_account} | Desc: {t.description}")
        if t.statement:
            print(f"  Stmt Acc: {t.statement.account_number} | Stmt ID: {t.statement_id}")
