import pandas as pd
from io import BytesIO
from xhtml2pdf import pisa
from flask import make_response

def export_transactions_excel(transactions):
    rows = []
    for t in transactions:
        rows.append({
            'date': t.date.strftime('%Y-%m-%d %H:%M'),
            'type': t.type,
            'currency': t.currency.code if t.currency else '',
            'quantity': t.quantity,
            'total_local': t.total_value_local,
            'profit': t.profit
        })
    df = pd.DataFrame(rows)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Transactions')
        writer.save()
    output.seek(0)
    resp = make_response(output.read())
    resp.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    resp.headers['Content-Disposition'] = 'attachment; filename=transactions.xlsx'
    return resp

def export_expenses_excel(expenses):
    rows = []
    for e in expenses:
        rows.append({
            'date': e.date.strftime('%Y-%m-%d'),
            'category': e.category,
            'currency': e.currency.code if e.currency else '',
            'amount': e.amount,
            'notes': e.notes
        })
    df = pd.DataFrame(rows)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Expenses')
        writer.save()
    output.seek(0)
    resp = make_response(output.read())
    resp.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    resp.headers['Content-Disposition'] = 'attachment; filename=expenses.xlsx'
    return resp

def render_pdf_from_html(html):
    result = BytesIO()
    pisa.CreatePDF(html, dest=result)
    result.seek(0)
    resp = make_response(result.read())
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = 'attachment; filename=report.pdf'
    return resp
