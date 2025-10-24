# exchange_app_v2 - Upgraded

This is an upgraded Flask scaffold tailored for a currency exchange office.
Enhancements included:
- Expenses model and UI
- Cashbox tracking with balance updates per currency
- Reports page with Excel (transactions/expenses) and PDF summary exports
- Improved dashboard with quick stats, nicer cards and icons
- Dark / Light theme toggle persisted in localStorage
- RTL-friendly Arabic UI

To run locally:
1. python -m venv .venv
2. pip install -r requirements.txt
3. set FLASK_APP=app.py (or export FLASK_APP=app.py)
4. python init_db.py
5. flask run
