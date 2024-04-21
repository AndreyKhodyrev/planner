from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField, DateField, IntegerRangeField, RadioField
from wtforms.validators import DataRequired


class CategoriesForm(FlaskForm):
    name = StringField("Название категории")
    submit = SubmitField('Готово')
