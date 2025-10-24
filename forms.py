from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, SelectField, TextAreaField, SubmitField, DateField, BooleanField
from wtforms.validators import DataRequired, Length, Optional
class LoginForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired()])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    submit = SubmitField('تسجيل الدخول')


class UserForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(max=80)])
    password = PasswordField('كلمة المرور', validators=[Optional()])
    role = SelectField('الدور', choices=[
        ('admin', 'مدير'),
        ('editor', 'محرر'),
        ('viewer', 'عارض')
    ], validators=[DataRequired()])
    submit = SubmitField('حفظ المستخدم')


class SettingsForm(FlaskForm):
    company_name = StringField('اسم الشركة', validators=[DataRequired(), Length(max=100)])
    company_logo = StringField('رمز الشركة (Bootstrap Icon)', validators=[DataRequired(), Length(max=200)])
    submit = SubmitField('حفظ الإعدادات')


class CurrencyForm(FlaskForm):
    code = StringField('رمز العملة', validators=[DataRequired(), Length(max=10)])
    name = StringField('اسم العملة', validators=[DataRequired(), Length(max=64)])
    rate = FloatField('سعر الصرف', validators=[DataRequired()])
    submit = SubmitField('حفظ العملة')


class TransactionForm(FlaskForm):
    type = SelectField('نوع العملية', choices=[
        ('buy', 'شراء'),
        ('sell', 'بيع')
    ], validators=[DataRequired()])
    currency_id = SelectField('العملة', coerce=int, validators=[DataRequired()])
    quantity = FloatField('الكمية', validators=[DataRequired()])
    buy_rate = FloatField('سعر الشراء')
    sell_rate = FloatField('سعر البيع')
    notes = TextAreaField('ملاحظات')
    submit = SubmitField('تسجيل العملية')


class ExpenseForm(FlaskForm):
    date = DateField('التاريخ', format='%Y-%m-%d')
    category = StringField('التصنيف', validators=[DataRequired(), Length(max=64)])
    amount = FloatField('المبلغ', validators=[DataRequired()])
    currency_id = SelectField('العملة', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('ملاحظات')
    submit = SubmitField('حفظ المصروف')

class DebtForm(FlaskForm):
    person_name = StringField('اسم الشخص', validators=[DataRequired(), Length(max=100)])
    amount = FloatField('المبلغ', validators=[DataRequired()])
    currency_id = SelectField('العملة', coerce=int, validators=[DataRequired()])
    due_date = DateField('تاريخ الاستحقاق', format='%Y-%m-%d', validators=[Optional()])
    notes = TextAreaField('ملاحظات')
    is_paid = BooleanField('تم السداد')
    submit = SubmitField('حفظ الدين')