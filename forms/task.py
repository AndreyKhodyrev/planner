from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField, DateField, IntegerRangeField, RadioField
from wtforms.validators import DataRequired


class TasksForm(FlaskForm):
    task = TextAreaField("Задача", validators=[DataRequired()])
    date = DateField("Дата выполнения")
    category = RadioField("Категория")
    importance = RadioField("Важность", choices=['Обязательно', 'Желательно', 'Как получится'])
    submit = SubmitField('Готово')
