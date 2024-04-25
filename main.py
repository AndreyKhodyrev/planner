from flask import Flask, render_template, redirect, session, make_response, request, Response, render_template_string
from flask_restful import Api, abort
from requests import get

from data import db_session, tasks_resources
from data.category import Category
from data.users import User
from data.tasks import Tasks
from forms.category import CategoriesForm
from forms.user import RegisterForm, LoginForm
from forms.task import TasksForm
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import datetime
import pandas as pd

app = Flask(__name__)
api = Api(app)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/session_test")
def session_test():
    visits_count = session.get('visits_count', 0)
    session['visits_count'] = visits_count + 1
    return make_response(
        f"Вы пришли на эту страницу {visits_count + 1} раз")


@app.route("/")
def index1():
    db_sess = db_session.create_session()
    tasks = db_sess.query(Tasks)
    category = db_sess.query(Category)
    try:
        sz = len(tasks.filter(Tasks.user_id == current_user.id).all())
    except:
        sz = 0
    date = datetime.datetime.now()
    date -= datetime.timedelta(days=1)
    lst = get('http://127.0.0.1:8080/api/tasks').json()['tasks']
    dct = [0, 0, 0]
    try:
        for item in lst:
            if item['user_id'] == current_user.id:
                if not item['is_complete'] and datetime.datetime.strptime(item['date'],
                                                                          '%a, %d %b %Y %H:%M:%S %Z') < date:
                    dct[2] += 1
                elif not item['is_complete']:
                    dct[1] += 1
                else:
                    dct[0] += 1
    except:
        pass
    dct.append(sum(dct))
    return render_template("index.html", tasks=tasks, category=category, category_id=0, name='Все задачи',
                           current_date=date, sz=sz, dct=dct)


@app.route("/<category_id>")
def index(category_id):
    db_sess = db_session.create_session()
    tasks = db_sess.query(Tasks)
    category = db_sess.query(Category)
    try:
        sz = len(tasks.filter(Tasks.user_id == current_user.id, Tasks.category_id == int(category_id)).all())
    except:
        sz = 0
        return abort(404)
    date = datetime.datetime.now()
    date -= datetime.timedelta(days=1)
    lst = get('http://127.0.0.1:8080/api/tasks').json()['tasks']
    dct = [0, 0, 0]
    try:
        for item in lst:
            if item['user_id'] == current_user.id and item['category_id'] == int(category_id):
                if not item['is_complete'] and datetime.datetime.strptime(item['date'],
                                                                          '%a, %d %b %Y %H:%M:%S %Z') < date:
                    dct[2] += 1
                elif not item['is_complete']:
                    dct[1] += 1
                else:
                    dct[0] += 1
    except:
        pass
    dct.append(sum(dct))
    name = db_sess.query(Category).filter(Category.id == int(category_id)).first().name
    return render_template("index.html", tasks=tasks, category=category, category_id=int(category_id),
                           name=name, current_date=date, sz=sz, dct=dct)


@app.route('/tasks_delete/<int:id>/<int:category_id>', methods=['GET', 'POST'])
@login_required
def tasks_delete(id, category_id):
    db_sess = db_session.create_session()
    tasks = db_sess.query(Tasks).filter(Tasks.id == id,
                                        Tasks.user == current_user
                                        ).first()
    if tasks:
        db_sess.delete(tasks)
        db_sess.commit()
    else:
        abort(404)
    if category_id != 0:
        return redirect('/' + str(category_id))
    return redirect('/')


@app.route('/download/<int:category_id>', methods=['GET', 'POST'])
@login_required
def download(category_id):
    db_sess = db_session.create_session()
    tasks = db_sess.query(Tasks).filter((Tasks.category_id == category_id) | (category_id == 0),
                                        Tasks.user == current_user
                                        ).all()
    lst = []
    for i in tasks:
        lst.append(
            {"Категория": db_sess.query(Category).filter(Category.id == i.category_id).first().name,
             "Задача": i.task, "Дата": str(i.date.date()), "Важность": i.importance})
    tr = {'Обязательно': 1, 'Желательно': 2, "Как получится": 3}
    lst.sort(key=lambda x: [x["Категория"], x["Дата"], tr[x["Важность"]]])
    dct = {"Категория": [], "Задача": [], "Дата": [], "Важность": []}
    for i in lst:
        dct["Категория"].append(i["Категория"])
        dct["Задача"].append(i["Задача"])
        dct["Дата"].append(i["Дата"])
        dct["Важность"].append(i["Важность"])
    df = pd.DataFrame(dct)
    return Response(
        df.to_csv(index=False, sep=';').encode('cp1251'),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=planner.csv"})


@app.route('/complete/<int:id>/<int:category_id>', methods=['GET', 'POST'])
@login_required
def tasks_complete(id, category_id):
    db_sess = db_session.create_session()
    tasks = db_sess.query(Tasks).filter(Tasks.id == id,
                                        Tasks.user == current_user
                                        ).first()
    if tasks:
        tasks.is_complete = not tasks.is_complete
        db_sess.commit()
    else:
        abort(404)
    if category_id != 0:
        return redirect('/' + str(category_id))
    return redirect('/')


@app.route('/tasks/<int:id>/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_tasks(id, category_id):
    form = TasksForm()
    db_sess = db_session.create_session()
    lst = db_sess.query(Category).filter(Category.user_id == current_user.id)
    lst2 = []
    for i in lst:
        lst2.append(i.name)
    form.category.choices = lst2
    if request.method == "GET":
        tasks = db_sess.query(Tasks).filter(Tasks.id == id,
                                            Tasks.user == current_user
                                            ).first()
        if tasks:
            form.task.data = tasks.task
            form.date.data = tasks.date
            form.category.data = db_sess.query(Category).filter(Category.id == tasks.category_id).first().name
            form.importance.data = tasks.importance
        else:
            abort(404)
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        tasks = db_sess.query(Tasks).filter(Tasks.id == id,
                                            Tasks.user == current_user
                                            ).first()
        if tasks:
            tasks.task = form.task.data
            tasks.date = form.date.data
            tasks.category_id = db_sess.query(Category).filter(Category.name == form.category.data).first().id
            tasks.importance = form.importance.data
            db_sess.commit()
            if category_id != 0:
                return redirect('/' + str(category_id))
            return redirect('/')
        else:
            abort(404)
    return render_template('tasks.html',
                           title='Редактирование задачи',
                           form=form
                           )


@app.route('/tasks/<category_id>', methods=['GET', 'POST'])
@login_required
def add_tasks(category_id):

    db_sess = db_session.create_session()
    if len(db_sess.query(Category).filter(Category.user_id == current_user.id).all()) == 0:
        if category_id == '0':
            return redirect('/')
        return redirect('/' + category_id)
    form = TasksForm()
    lst = db_sess.query(Category).filter(Category.user_id == current_user.id)
    lst2 = []
    for i in lst:
        lst2.append(i.name)
    form.category.choices = lst2
    if category_id != '0':
        form.category.choices = [db_sess.query(Category).filter(Category.id == int(category_id)).first().name]
    if form.validate_on_submit():
        tasks = Tasks()
        tasks.task = form.task.data
        tasks.date = form.date.data
        tasks.category_id = db_sess.query(Category).filter(Category.name == form.category.data,
                                                           Category.user_id == current_user.id).first().id
        tasks.importance = form.importance.data
        tasks.is_complete = False
        current_user.tasks.append(tasks)
        db_sess.merge(current_user)
        db_sess.commit()
        if category_id == '0':
            return redirect('/')
        return redirect('/' + category_id)
    return render_template('tasks.html', title='Добавление задачи',
                           form=form, category_id=int(category_id))


@app.route('/categories', methods=['GET', 'POST'])
@login_required
def add_categories():
    db_sess = db_session.create_session()
    form = CategoriesForm()
    if form.validate_on_submit() and not (
            db_sess.query(Category).filter(Category.user_id == current_user.id, Category.name == form.name.data).all()):
        categories = Category()
        categories.name = form.name.data
        current_user.categories.append(categories)
        db_sess.merge(current_user)
        db_sess.commit()
        return redirect('/')
    return render_template('categories.html', title='Добавление категории',
                           form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


def main():
    db_session.global_init("db/planner.db")
    api.add_resource(tasks_resources.TasksListResource, '/api/tasks')
    app.run(host='0.0.0.0', port=8080)


if __name__ == '__main__':
    main()
