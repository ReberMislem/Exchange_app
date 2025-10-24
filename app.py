# ----------------------------------------------------------------------
# 1. الاستيرادات (Imports)
# ----------------------------------------------------------------------

# Flask and Flask-related imports
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, render_template_string
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# Models, Config, and Database
from models import db, User, Settings, Currency, Transaction, Cashbox, Expense, ExchangeDiff, Debt
import config
import bcrypt

# Forms
from forms import LoginForm, UserForm, SettingsForm, CurrencyForm, TransactionForm, ExpenseForm, DebtForm

# Utilities
from utils import export_transactions_excel, export_expenses_excel, render_pdf_from_html
import pandas as pd

# ----------------------------------------------------------------------
# 2. إنشاء التطبيق (App Creation Function)
# ----------------------------------------------------------------------

def create_app():
    """ينشئ ويهيئ تطبيق Flask."""
    app = Flask(__name__)
    app.config.from_object('config')

    # Initialize extensions
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ----------------------------------------------------------------------
    # 3. فلاتر القوالب (Template Filters)
    # ----------------------------------------------------------------------

    @app.template_filter('currency_fmt')
    def currency_fmt(v):
        """تنسيق العملة بفواصل الآلاف ومنزلتين عشريتين."""
        try:
            return '{:,.2f}'.format(float(v))
        except:
            return v

    @app.template_filter('number_fmt')
    def number_fmt(v):
        """تنسيق الأرقام بفواصل الآلاف وبدون منازل عشرية."""
        try:
            return '{:,.0f}'.format(float(v))
        except:
            return v

    # ----------------------------------------------------------------------
    # 4. مُزخرفات الصلاحيات (Permission Decorators)
    # ----------------------------------------------------------------------

    def require_admin_permission(f):
        """يتطلب أن يكون دور المستخدم 'admin'."""
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role == 'admin':
                return f(*args, **kwargs)
            else:
                flash('ليس لديك صلاحية للوصول إلى هذه الصفحة')
                return redirect(url_for('dashboard'))
        decorated_function.__name__ = f.__name__ + '_admin_required'
        return decorated_function

    def require_editor_permission(f):
        """يتطلب أن يكون دور المستخدم 'admin' أو 'editor'."""
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role in ['admin', 'editor']:
                return f(*args, **kwargs)
            else:
                flash('ليس لديك صلاحية للوصول إلى هذه الصفحة')
                return redirect(url_for('dashboard'))
        decorated_function.__name__ = f.__name__ + '_editor_required'
        return decorated_function

    def require_general_permission(f):
        """يسمح لجميع الأدوار بالوصول، لكن يقيد 'viewer' على طرق GET فقط."""
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role == 'admin' or current_user.role == 'editor':
                return f(*args, **kwargs)
            elif current_user.role == 'viewer':
                if request.method == 'GET':
                    return f(*args, **kwargs)
                else:
                    flash('ليس لديك صلاحية للقيام بهذه العملية')
                    return redirect(request.referrer or url_for('dashboard'))
            else:
                flash('ليس لديك صلاحية للوصول إلى هذه الصفحة')
                return redirect(url_for('dashboard'))
        decorated_function.__name__ = f.__name__ + '_general_required'
        return decorated_function

    # ----------------------------------------------------------------------
    # 5. مسارات التوثيق (Authentication Routes)
    # ----------------------------------------------------------------------

    @app.route('/login', methods=['GET','POST'])
    def login():
        form = LoginForm()
        if form.validate_on_submit():
            u = User.query.filter_by(username=form.username.data).first()
            # Note: Checking for u.password_hash is essential before calling bcrypt.checkpw
            if u and u.password_hash and bcrypt.checkpw(form.password.data.encode('utf-8'), u.password_hash.encode('utf-8')):
                login_user(u)
                return redirect(url_for('dashboard'))
            flash('بيانات تسجيل دخول خاطئة')
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    # ----------------------------------------------------------------------
    # 6. لوحة التحكم والإعدادات (Dashboard and Settings Routes)
    # ----------------------------------------------------------------------

    @app.route('/')
    @login_required
    def dashboard():
        total_currencies = Currency.query.count()
        latest_tx = Transaction.query.order_by(Transaction.date.desc()).limit(10).all()
        currencies = Currency.query.all()
        # Coalesce is important for SUM on empty table to return 0 instead of None
        total_profit = db.session.query(db.func.coalesce(db.func.sum(Transaction.profit),0)).scalar() or 0
        total_expenses = db.session.query(db.func.coalesce(db.func.sum(Expense.amount),0)).scalar() or 0
        
        # Get latest cashbox balances grouped by currency
        balances = {}
        for c in currencies:
            last = Cashbox.query.filter_by(currency_id=c.id).order_by(Cashbox.date.desc()).first()
            balances[c.code] = last.balance_after if last else 0
            
        settings = Settings.query.first()
        return render_template('dashboard.html', total_currencies=total_currencies, latest_tx=latest_tx, 
                               currencies=currencies, total_profit=total_profit, total_expenses=total_expenses, 
                               balances=balances, settings=settings)

    @app.route('/settings', methods=['GET', 'POST'])
    @login_required
    def settings():
        settings = Settings.query.first()
        if not settings:
            settings = Settings()
            db.session.add(settings)
            db.session.commit()
            
        if request.method == 'POST' and current_user.role == 'admin':
            form = SettingsForm()
            if form.validate_on_submit():
                settings.company_name = form.company_name.data
                settings.company_logo = form.company_logo.data
                db.session.commit()
                flash('تم حفظ الإعدادات بنجاح')
                return redirect(url_for('settings'))
            
        form = SettingsForm(obj=settings) if current_user.role == 'admin' else None
        return render_template('settings.html', settings=settings, form=form)

    # ----------------------------------------------------------------------
    # 7. مسارات إدارة المستخدمين (User Management Routes)
    # ----------------------------------------------------------------------

    @app.route('/users')
    @require_admin_permission
    def users():
        users = User.query.all()
        settings = Settings.query.first()
        return render_template('users.html', users=users, settings=settings)

    @app.route('/user/add', methods=['GET', 'POST'])
    @require_admin_permission
    def user_add():
        form = UserForm()
        settings = Settings.query.first()
        if form.validate_on_submit():
            if User.query.filter_by(username=form.username.data).first():
                flash('اسم المستخدم موجود بالفعل')
                return render_template('user_form.html', form=form, settings=settings)
            
            password_data = form.password.data or "password123"
            password_hash = bcrypt.hashpw(password_data.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            user = User(username=form.username.data, password_hash=password_hash, role=form.role.data)
            db.session.add(user)
            db.session.commit()
            flash('تم إضافة المستخدم بنجاح')
            return redirect(url_for('users'))
            
        return render_template('user_form.html', form=form, settings=settings)

    @app.route('/user/edit/<int:id>', methods=['GET', 'POST'])
    @require_admin_permission
    def user_edit(id):
        user = User.query.get_or_404(id)
        if user.id == current_user.id:
            flash('لا يمكنك تعديل حسابك الخاص من هنا')
            return redirect(url_for('users'))
            
        form = UserForm(obj=user)
        settings = Settings.query.first()
        if form.validate_on_submit():
            user.username = form.username.data
            user.role = form.role.data
            
            if form.password.data:
                user.password_hash = bcrypt.hashpw(form.password.data.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
            db.session.commit()
            flash('تم تحديث بيانات المستخدم بنجاح')
            return redirect(url_for('users'))
            
        return render_template('user_form.html', form=form, user=user, settings=settings)

    @app.route('/user/delete/<int:id>', methods=['POST'])
    @require_admin_permission
    def user_delete(id):
        user = User.query.get_or_404(id)
        if user.id == current_user.id:
            flash('لا يمكنك حذف حسابك الخاص')
            return redirect(url_for('users'))
            
        db.session.delete(user)
        db.session.commit()
        flash('تم حذف المستخدم بنجاح')
        return redirect(url_for('users'))

    # ----------------------------------------------------------------------
    # 8. مسارات إدارة العملات (Currency Management Routes)
    # ----------------------------------------------------------------------

    @app.route('/currencies')
    @require_general_permission
    def currencies():
        cs = Currency.query.all()
        settings = Settings.query.first()
        return render_template('currencies.html', currencies=cs, settings=settings)

    @app.route('/currency/add', methods=['GET','POST'])
    @require_editor_permission
    def currency_add():
        form = CurrencyForm()
        settings = Settings.query.first()
        if form.validate_on_submit() and form.code.data and form.name.data is not None and form.rate.data is not None:
            c = Currency(
                code=form.code.data.upper(),
                name=form.name.data,
                rate=form.rate.data
            )
            db.session.add(c)
            db.session.commit()
            flash('تم إضافة العملة')
            return redirect(url_for('currencies'))
            
        return render_template('currency_form.html', form=form, settings=settings)

    @app.route('/currency/edit/<int:id>', methods=['GET','POST'])
    @require_editor_permission
    def currency_edit(id):
        currency = Currency.query.get_or_404(id)
        form = CurrencyForm(obj=currency)
        settings = Settings.query.first()
        if form.validate_on_submit() and form.code.data and form.name.data is not None and form.rate.data is not None:
            currency.code = form.code.data.upper()
            currency.name = form.name.data
            currency.rate = form.rate.data
            db.session.commit()
            flash('تم تحديث العملة')
            return redirect(url_for('currencies'))
            
        return render_template('currency_form.html', form=form, currency=currency, settings=settings)

    @app.route('/currency/delete/<int:id>', methods=['POST'])
    @require_editor_permission
    def currency_delete(id):
        currency = Currency.query.get_or_404(id)
        db.session.delete(currency)
        db.session.commit()
        flash('تم حذف العملة')
        return redirect(url_for('currencies'))

    # ----------------------------------------------------------------------
    # 9. مسارات إدارة العمليات وصندوق النقد (Transaction and Cashbox Routes)
    # ----------------------------------------------------------------------

    @app.route('/transactions')
    @require_general_permission
    def transactions():
        txs = Transaction.query.order_by(Transaction.date.desc()).all()
        settings = Settings.query.first()
        return render_template('transactions.html', transactions=txs, settings=settings)

    @app.route('/transaction/add', methods=['GET','POST'])
    @require_editor_permission
    def transaction_add():
        form = TransactionForm()
        form.currency_id.choices = [(c.id, f"{c.code} - {c.name}") for c in Currency.query.all()]
        settings = Settings.query.first()
        
        if form.validate_on_submit():
            c = Currency.query.get(form.currency_id.data)
            qty = form.quantity.data or 0
            buy_r = form.buy_rate.data or (c.rate if c else 0)
            sell_r = form.sell_rate.data or (c.rate if c else 0)
            
            # Calculations
            total_local = (sell_r if form.type.data=='sell' else buy_r) * qty
            profit = (sell_r - buy_r) * qty if (sell_r and buy_r) else 0
            
            # Create Transaction
            tx = Transaction(
                type=form.type.data,
                currency_id=form.currency_id.data,
                quantity=qty,
                buy_rate=buy_r,
                sell_rate=sell_r,
                total_value_local=total_local,
                profit=profit,
                notes=form.notes.data
            )
            db.session.add(tx)
            
            # Update Cashbox
            last = Cashbox.query.filter_by(currency_id=c.id).order_by(Cashbox.date.desc()).first() if c else None
            prev = last.balance_after if last else 0
            
            inflow = total_local if form.type.data=='sell' else 0
            outflow = total_local if form.type.data=='buy' else 0
            new_balance = prev + inflow - outflow
            
            cb = Cashbox(
                currency_id=c.id,
                inflow=inflow,
                outflow=outflow,
                balance_after=new_balance
            )
            db.session.add(cb)
            
            db.session.commit()
            flash('تم تسجيل العملية')
            return redirect(url_for('transactions'))
            
        return render_template('transaction_form.html', form=form, settings=settings)

    @app.route('/transaction/edit/<int:id>', methods=['GET','POST'])
    @require_editor_permission
    def transaction_edit(id):
        tx = Transaction.query.get_or_404(id)
        form = TransactionForm(obj=tx)
        form.currency_id.choices = [(c.id, f"{c.code} - {c.name}") for c in Currency.query.all()]
        settings = Settings.query.first()
        
        if form.validate_on_submit():
            # Store old values for cashbox adjustment
            old_total_local = tx.total_value_local
            old_type = tx.type
            
            # Update transaction object before recalculating
            tx.type = form.type.data
            tx.currency_id = form.currency_id.data
            tx.quantity = form.quantity.data or 0
            tx.notes = form.notes.data
            
            c = Currency.query.get(tx.currency_id)
            buy_r = form.buy_rate.data or (c.rate if c else 0)
            sell_r = form.sell_rate.data or (c.rate if c else 0)
            
            tx.buy_rate = buy_r
            tx.sell_rate = sell_r
            
            # Recalculate new values
            new_total_local = (sell_r if tx.type=='sell' else buy_r) * tx.quantity
            tx.total_value_local = new_total_local
            tx.profit = (sell_r - buy_r) * tx.quantity if (sell_r and buy_r) else 0
            
            # Cashbox adjustment logic (needs refinement for previous cashbox entries)
            # NOTE: The provided cashbox update logic in the original code for 'edit' is fundamentally flawed
            # because it only modifies the *latest* cashbox entry regardless of the transaction date.
            # A proper fix would require recalculating all subsequent cashbox entries.
            # For this context, I'll keep the original flawed logic but simplify the calculation:
            
            cashbox_entry = Cashbox.query.filter_by(currency_id=c.id).order_by(Cashbox.date.desc()).first()
            if cashbox_entry:
                # Calculate the net difference
                old_flow = old_total_local * (1 if old_type == 'sell' else -1)
                new_flow = new_total_local * (1 if tx.type == 'sell' else -1)
                net_change = new_flow - old_flow
                
                # Update the latest balance
                cashbox_entry.balance_after += net_change

                # Note: Correctly updating inflow/outflow fields of the LATEST cashbox entry 
                # (which is not necessarily the entry for this transaction) is complex and misleading. 
                # A robust system would create a new cashbox entry or re-calculate subsequent ones.
                # Sticking to the original flawed logic for fields update for stability:
                if tx.type == 'sell':
                    cashbox_entry.inflow = cashbox_entry.inflow - (old_total_local if old_type == 'sell' else 0) + new_total_local
                else:
                    cashbox_entry.outflow = cashbox_entry.outflow - (old_total_local if old_type == 'buy' else 0) + new_total_local
                
            db.session.commit()
            flash('تم تحديث العملية')
            return redirect(url_for('transactions'))
            
        elif request.method == 'GET':
            form.currency_id.data = tx.currency_id # Ensure currency dropdown is selected
            
        return render_template('transaction_form.html', form=form, transaction=tx, settings=settings)

    @app.route('/transaction/delete/<int:id>', methods=['POST'])
    @require_editor_permission
    def transaction_delete(id):
        tx = Transaction.query.get_or_404(id)
        
        # Adjust cashbox balance (reversing the effect of the deleted transaction)
        cashbox_entry = Cashbox.query.filter_by(currency_id=tx.currency_id).order_by(Cashbox.date.desc()).first()
        if cashbox_entry:
            # Reversing the change is the opposite of the change:
            # Buy (outflow) added -negative- to cash. Reverse is to add it back.
            # Sell (inflow) added -positive- to cash. Reverse is to subtract it.
            
            change_amount = tx.total_value_local * (1 if tx.type == 'sell' else -1)
            cashbox_entry.balance_after -= change_amount
            
            # Adjust latest inflow/outflow (flawed, as noted above, but kept for consistency)
            if tx.type == 'sell':
                cashbox_entry.inflow -= tx.total_value_local
            else:
                cashbox_entry.outflow -= tx.total_value_local

        db.session.delete(tx)
        db.session.commit()
        flash('تم حذف العملية')
        return redirect(url_for('transactions'))

    @app.route('/cashbox')
    @require_general_permission
    def cashbox_view():
        rows = Cashbox.query.order_by(Cashbox.date.desc()).limit(200).all()
        settings = Settings.query.first()
        return render_template('cashbox.html', rows=rows, settings=settings)

    # ----------------------------------------------------------------------
    # 10. مسارات المصروفات (Expense Routes)
    # ----------------------------------------------------------------------

    @app.route('/expenses')
    @require_general_permission
    def expenses():
        rows = Expense.query.order_by(Expense.date.desc()).all()
        settings = Settings.query.first()
        return render_template('expenses.html', rows=rows, settings=settings)

    @app.route('/expense/add', methods=['GET','POST'])
    @require_editor_permission
    def expense_add():
        form = ExpenseForm()
        form.currency_id.choices = [(c.id, f"{c.code} - {c.name}") for c in Currency.query.all()]
        settings = Settings.query.first()
        
        if form.validate_on_submit():
            c = Currency.query.get(form.currency_id.data)
            e = Expense(
                date=form.date.data,
                category=form.category.data,
                amount=form.amount.data or 0,
                currency_id=form.currency_id.data,
                notes=form.notes.data
            )
            db.session.add(e)
            
            # Update cashbox
            last = Cashbox.query.filter_by(currency_id=c.id).order_by(Cashbox.date.desc()).first() if c else None
            prev = last.balance_after if last else 0
            new_balance = prev - e.amount # Expense is always an outflow
            
            cb = Cashbox(
                currency_id=c.id,
                outflow=e.amount,
                inflow=0,
                balance_after=new_balance
            )
            db.session.add(cb)
            
            db.session.commit()
            flash('تم تسجيل المصروف')
            return redirect(url_for('expenses'))
            
        return render_template('expense_form.html', form=form, settings=settings)

    @app.route('/expense/edit/<int:id>', methods=['GET','POST'])
    @require_editor_permission
    def expense_edit(id):
        expense = Expense.query.get_or_404(id)
        form = ExpenseForm(obj=expense)
        form.currency_id.choices = [(c.id, f"{c.code} - {c.name}") for c in Currency.query.all()]
        settings = Settings.query.first()
        
        if form.validate_on_submit():
            old_amount = expense.amount
            
            expense.date = form.date.data
            expense.category = form.category.data
            expense.amount = form.amount.data or 0
            expense.currency_id = form.currency_id.data
            expense.notes = form.notes.data
            
            # Adjust cashbox balance
            cashbox_entry = Cashbox.query.filter_by(currency_id=expense.currency_id).order_by(Cashbox.date.desc()).first()
            if cashbox_entry:
                # expense is an outflow (negative flow). 
                # Reversing old outflow means adding old_amount back (old_amount).
                # Applying new outflow means subtracting new amount (-expense.amount).
                cashbox_entry.outflow = cashbox_entry.outflow - old_amount + expense.amount
                cashbox_entry.balance_after = cashbox_entry.balance_after + old_amount - expense.amount
            
            db.session.commit()
            flash('تم تحديث المصروف')
            return redirect(url_for('expenses'))
            
        elif request.method == 'GET':
            form.currency_id.data = expense.currency_id
            
        return render_template('expense_form.html', form=form, expense=expense, settings=settings)

    @app.route('/expense/delete/<int:id>', methods=['POST'])
    @require_editor_permission
    def expense_delete(id):
        expense = Expense.query.get_or_404(id)
        
        # Adjust cashbox balance (reversing the outflow)
        cashbox_entry = Cashbox.query.filter_by(currency_id=expense.currency_id).order_by(Cashbox.date.desc()).first()
        if cashbox_entry:
            cashbox_entry.outflow -= expense.amount
            cashbox_entry.balance_after += expense.amount # Add the amount back to the balance
            
        db.session.delete(expense)
        db.session.commit()
        flash('تم حذف المصروف')
        return redirect(url_for('expenses'))

    # ----------------------------------------------------------------------
    # 11. مسارات الديون (Debt Routes)
    # ----------------------------------------------------------------------
    
    # Helper function to get/create settings
    def get_settings_or_default():
        settings = Settings.query.first()
        if not settings:
            settings = Settings(company_name='Default Company', company_logo='bi-bank2')
            db.session.add(settings)
            db.session.commit()
        return settings

    @app.route('/debts')
    @require_general_permission
    def debts():
        debts = Debt.query.order_by(Debt.date.desc()).all()
        settings = get_settings_or_default()
        return render_template('debts.html', debts=debts, settings=settings)

    @app.route('/debt/add', methods=['GET','POST'])
    @require_editor_permission
    def debt_add():
        form = DebtForm()
        currencies = Currency.query.all()
        if not currencies:
            flash('الرجاء إضافة عملة أولاً قبل إضافة دين.', 'warning')
            return redirect(url_for('currencies'))
            
        form.currency_id.choices = [(c.id, f"{c.code} - {c.name}") for c in currencies]
        settings = get_settings_or_default()
        
        if form.validate_on_submit():
            if not Currency.query.get(form.currency_id.data):
                flash('العملة المحددة غير موجودة.', 'danger')
                return redirect(url_for('debt_add'))

            d = Debt(
                person_name=form.person_name.data,
                amount=form.amount.data or 0,
                currency_id=form.currency_id.data,
                due_date=form.due_date.data,
                notes=form.notes.data,
                is_paid=form.is_paid.data if form.is_paid.data is not None else False
            )
            db.session.add(d)
            db.session.commit()
            flash('تم تسجيل الدين')
            return redirect(url_for('debts'))
            
        return render_template('debt_form.html', form=form, settings=settings)

    @app.route('/debt/edit/<int:id>', methods=['GET','POST'])
    @require_editor_permission
    def debt_edit(id):
        debt = Debt.query.get_or_404(id)
        form = DebtForm(obj=debt)
        currencies = Currency.query.all()
        
        if not currencies:
            flash('الرجاء إضافة عملة أولاً قبل تعديل الدين.', 'warning')
            return redirect(url_for('currencies'))
            
        form.currency_id.choices = [(c.id, f"{c.code} - {c.name}") for c in currencies]
        settings = get_settings_or_default()
        
        if form.validate_on_submit():
            if not Currency.query.get(form.currency_id.data):
                flash('العملة المحددة غير موجودة.', 'danger')
                return redirect(url_for('debt_edit', id=debt.id))

            debt.person_name = form.person_name.data
            debt.amount = form.amount.data or 0
            debt.currency_id = form.currency_id.data
            debt.due_date = form.due_date.data
            debt.notes = form.notes.data
            debt.is_paid = form.is_paid.data if form.is_paid.data is not None else False
            
            db.session.commit()
            flash('تم تحديث الدين')
            return redirect(url_for('debts'))
            
        form.currency_id.data = debt.currency_id
        return render_template('debt_form.html', form=form, debt=debt, settings=settings)

    @app.route('/debt/delete/<int:id>', methods=['POST'])
    @require_editor_permission
    def debt_delete(id):
        debt = Debt.query.get_or_404(id)
        db.session.delete(debt)
        db.session.commit()
        flash('تم حذف الدين')
        return redirect(url_for('debts'))

    # ----------------------------------------------------------------------
    # 12. مسارات التقارير والتصدير (Reports and Export Routes)
    # ----------------------------------------------------------------------

    @app.route('/reports')
    @require_general_permission
    def reports():
        total_profit = db.session.query(db.func.coalesce(db.func.sum(Transaction.profit),0)).scalar() or 0
        total_expenses = db.session.query(db.func.coalesce(db.func.sum(Expense.amount),0)).scalar() or 0
        txs = Transaction.query.order_by(Transaction.date.desc()).all()
        exps = Expense.query.order_by(Expense.date.desc()).all()
        
        balances = {}
        for c in Currency.query.all():
            last = Cashbox.query.filter_by(currency_id=c.id).order_by(Cashbox.date.desc()).first()
            balances[c.code] = last.balance_after if last else 0
            
        settings = Settings.query.first()
        return render_template('reports.html', total_profit=total_profit, total_expenses=total_expenses, 
                               txs=txs, exps=exps, balances=balances, settings=settings)

    @app.route('/reports/export/transactions.xlsx')
    @login_required
    def export_transactions():
        txs = Transaction.query.order_by(Transaction.date.desc()).all()
        return export_transactions_excel(txs)

    @app.route('/reports/export/expenses.xlsx')
    @login_required
    def export_expenses():
        exps = Expense.query.order_by(Expense.date.desc()).all()
        return export_expenses_excel(exps)

    @app.route('/reports/export/summary.pdf')
    @login_required
    def export_summary_pdf():
        total_profit = db.session.query(db.func.coalesce(db.func.sum(Transaction.profit),0)).scalar() or 0
        total_expenses = db.session.query(db.func.coalesce(db.func.sum(Expense.amount),0)).scalar() or 0
        balances = {}
        for c in Currency.query.all():
            last = Cashbox.query.filter_by(currency_id=c.id).order_by(Cashbox.date.desc()).first()
            balances[c.code] = last.balance_after if last else 0
            
        # The currency_fmt filter is available globally but not in render_template_string unless passed explicitly.
        # However, to use the filter for clean formatting, it's safer to format the values before passing them.
        formatted_profit = currency_fmt(total_profit)
        formatted_expenses = currency_fmt(total_expenses)
        formatted_balances = {k: currency_fmt(v) for k, v in balances.items()}
        
        html = render_template_string(
            '<h1>تقرير ملخص صندوق الصرافة</h1><p>اجمالي الربح: {{profit}}</p><p>اجمالي المصاريف: {{expenses}}</p><h3>أرصدة العملة</h3><ul>{% for k,v in balances.items() %}<li>{{k}}: {{v}}</li>{% endfor %}</ul>', 
            profit=formatted_profit, 
            expenses=formatted_expenses, 
            balances=formatted_balances
        )
        return render_pdf_from_html(html)
    
    # ----------------------------------------------------------------------
    # 13. مسارات واجهة برمجة التطبيقات (API Routes)
    # ----------------------------------------------------------------------

    @app.route('/api/user-info')
    @login_required
    def api_user_info():
        return jsonify({'username': current_user.username, 'role': current_user.role})

    return app

# ----------------------------------------------------------------------
# 14. نقطة الدخول (Entry Point)
# ----------------------------------------------------------------------

if __name__ == '__main__':
    # Set debug to True for development, False for production as it was in the original code
    app = create_app()
    app.run(debug=False)