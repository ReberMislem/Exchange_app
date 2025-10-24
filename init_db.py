# init_db.py
from app import create_app
from models import db, User, Currency, Cashbox, Expense, Transaction
import bcrypt
from datetime import datetime, timedelta, timezone
import random

app = create_app()
app.app_context().push()

# إنشاء الجداول
db.create_all()

# إضافة مستخدم admin إذا لم يكن موجود
if not User.query.filter_by(username='admin').first():
    pw = bcrypt.hashpw('admin123'.encode(), bcrypt.gensalt()).decode()
    u = User(username='admin', password_hash=pw, role='admin')
    db.session.add(u)

# إضافة العملات إذا لم تكن موجودة
currencies_data = [
    ('USD', 'دولار أمريكي', 10950),
    ('EUR', 'يورو', 10200),
    ('IQD', 'دينار عراقي', 1)
]

for code, name, rate in currencies_data:
    if not Currency.query.filter_by(code=code).first():
        c = Currency(code=code, name=name, rate=rate)
        db.session.add(c)

db.session.commit()

# جلب العملات
usd = Currency.query.filter_by(code='USD').first()
eur = Currency.query.filter_by(code='EUR').first()
iqd = Currency.query.filter_by(code='IQD').first()

# تعبئة الصندوق في حال عدم وجود أي بيانات
if not Cashbox.query.first():
    cb_entries = [
        Cashbox(currency=usd, inflow=0, outflow=0, balance_after=2000),
        Cashbox(currency=eur, inflow=0, outflow=0, balance_after=1500),
        Cashbox(currency=iqd, inflow=0, outflow=0, balance_after=5_000_000),
    ]
    db.session.add_all(cb_entries)
    db.session.commit()

# إضافة مصاريف تجريبية إذا لم تكن موجودة
if not Expense.query.first():
    expenses = [
        Expense(date=datetime.now(timezone.utc) - timedelta(days=2), category='إيجار', amount=500_000, currency=iqd, notes='إيجار المكتب'),
        Expense(date=datetime.now(timezone.utc) - timedelta(days=1), category='كهرباء', amount=120_000, currency=iqd, notes='فاتورة شهرية'),
        Expense(date=datetime.now(timezone.utc) - timedelta(days=3), category='صيانة', amount=75, currency=usd, notes='صيانة حاسوب'),
    ]
    db.session.add_all(expenses)
    db.session.commit()

    # تحديث الصندوق بعد المصاريف
    for e in expenses:
        last_cb = Cashbox.query.filter_by(currency_id=e.currency.id).order_by(Cashbox.date.desc()).first()
        prev_balance = last_cb.balance_after if last_cb else 0
        cb = Cashbox(
            currency=e.currency,
            inflow=0,
            outflow=e.amount,
            balance_after=prev_balance - e.amount
        )
        db.session.add(cb)
    db.session.commit()

# إضافة معاملات تجريبية إذا لم تكن موجودة
if not Transaction.query.first():
    for i in range(5):
        date = datetime.now(timezone.utc) - timedelta(days=i)
        qty = random.randint(100, 500)
        buy_r = usd.rate
        sell_r = usd.rate + random.randint(50, 200)
        total_local = sell_r * qty
        profit = (sell_r - buy_r) * qty

        t = Transaction(
            date=date,
            type='sell',
            currency=usd,
            quantity=qty,
            buy_rate=buy_r,
            sell_rate=sell_r,
            total_value_local=total_local,
            profit=profit,
            notes=f"عملية بيع رقم {i+1}"
        )
        db.session.add(t)

        # تحديث الصندوق بعد المعاملة
        last_cb = Cashbox.query.filter_by(currency_id=usd.id).order_by(Cashbox.date.desc()).first()
        prev_balance = last_cb.balance_after if last_cb else 0
        cb = Cashbox(
            currency=usd,
            inflow=total_local,
            outflow=0,
            balance_after=prev_balance + total_local
        )
        db.session.add(cb)

db.session.commit()

print("✅ Database initialized with demo data successfully!")
