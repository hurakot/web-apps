import random
import sqlite3
from flask import Flask, render_template, g, request, session, redirect, url_for, flash, get_flashed_messages
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from faker import Faker
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps
from visitor_log import visitor
from visitor_log import get_db
from models import db
from models import Users
from models import visit_logs


# нужно настроить журнал посещений так, 
# чтобы пользователь мог смотреть только свои записи, 
# а админ мог просматривать записи всех пользователей.


app = Flask(__name__)
app.config['SECRET_KEY'] = '12345'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lab5.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

DATABASE = "lab5.db"

app.register_blueprint(visitor, url_prefix='/visitor')

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'authorisation'

application = app

@login_manager.unauthorized_handler
def unauthorized():
    flash("Пройдите процедуру авторизации, чтобы получить доступ к странице.", "danger")
    return redirect(url_for('authorisation'))

with app.app_context():
    db.create_all()

def check_rights(roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):

            # Если не удалось зайти на страницу, то об этом не будет создаваться запись в БД.
            if not current_user.is_authenticated or current_user.role not in roles:
                # g.skip_log = True
                session['skip_log'] = True
                flash("У вас недостаточно прав для доступа к данной странице.", "danger")
                return redirect(url_for('index'))

            # 1. Проверка авторизации
            if not current_user.is_authenticated:
                flash("Сначала войдите в систему", "danger")
                return redirect(url_for('authorisation'))

            # 2. Проверка роли
            if current_user.role not in roles:
                flash("У вас недостаточно прав для доступа к данной странице.", "danger")
                return redirect(url_for('index'))

            # 3. Всё ок → выполняем функцию
            return f(*args, **kwargs)

        return wrapper
    return decorator

# #Не будет создавать запись в БД о том, что вы под ролью с недостаточными правами пытались зайти на страницы админа.
# def role_required(*roles):
#     def decorator(f):
#         @wraps(f)
#         def wrapper(*args, **kwargs):
#             if not current_user.is_authenticated or current_user.role not in roles:
#                 g.skip_log = True
#                 return redirect(url_for('index'))
#             return f(*args, **kwargs)
#         return wrapper
#     return decorator

#Загрузка пользователя, если он проходил авторизацию
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

#Действия, выполняемые перед запросом.
@app.before_request
def before_request():
    g.db = get_db()
    if current_user.is_authenticated:
        user_id = int(current_user.id)
    else:
        user_id = None

#Действия, выполняемые после запроса.
@app.after_request
def after_request(response):
    if current_user.is_authenticated:
        user_id = int(current_user.id)
    else:
        user_id = None
    if response.status_code == 200:
        # if getattr(g, "skip_log", False):
        #     return response
        if session.pop('skip_log', False):
            return response
        else:
            if request.endpoint != "visitor.visitor_log" and request.endpoint != "visitor.report_pages" and request.endpoint != "visitor.report_users" and request.endpoint != "static":
                log = visit_logs(
                    user_id = user_id,
                    path = request.url, #+ "/" + request.endpoint,
                    created_at = datetime.now()
                )
                db.session.add(log)
                db.session.commit()
    return response
    

#Проверка введённых данных
def check_exam(username, password):
    alphabet="abcdefghijklmnopqrstuvwxyz"
    ALPHABET="ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    numbers="0123456789"
    alphabet_rus="абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    ALPHABET_RUS="АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
    symbols = "~!?@#$%^&*_-+()[]{>}</\\|\"\'.,:;"

    count_user = 0 #Кол-во символов в логине
    count_pass = 0 #Кол-во символов в пароле

    small = 0 #Прописные буквы
    big = 0 #Строчные буквы
    number = 0 #Цифры

    correct = 0 #Счётчик, который показывает, что логин и пароль введены правильно

    point = [] #Список, в котором хранятся все ошибки

    if len(username) >= 5:
        for i in username:
            if i in alphabet or i in ALPHABET or i in numbers:
                count_user += 1
        if count_user != len(username):
            # return f"В логине могут быть только строчные и прописные буквы из латинского алфавита и цифры" #point.append(3) = 3
            point.append(3)
        else:
            correct += 1 #point.append(1) = 1
            point.append(1)
    else:
        # return f"Длина логина должна быть не менее 5 символов" #point.append(4) = 4
        point.append(4)
    
    if len(password) >= 8 and len(username) <= 128:
        for i in password:
            if i in symbols:
                count_pass += 1
            elif i in alphabet or i in alphabet_rus:
                count_pass += 1
                small += 1
            elif i in ALPHABET or i in ALPHABET_RUS:
                count_pass += 1
                big += 1
            elif i in numbers:
                count_pass += 1
                number += 1
        if count_pass == len(password):
            if small >= 1 and big >= 1 and number >= 1:
                correct += 1 #point.append(2) = 2
                point.append(2)
            else:
                # return f"В пароле должны быть 1 строчная буква, 1 прописная буква и 1 цифра" #point.append(7) = 7
                point.append(7)
        else:
            # return f"В пароле введены неправильные символы" #point.append(6) = 6
            point.append(6)
    else: 
        # return f"Пароль не соответствует размеру" #point.append(5) = 5
        point.append(5)
    
    return point
    # if correct == 2:
    #     return f"Данные введены правильно"


    

@app.route('/')
def beginning():
    data = Users.query.all()
    if current_user.is_authenticated:
        id = current_user.id
        role = current_user.role
        authorisation = "user"
    else:
        authorisation = "anonymous"
        id = 0
        role = "none"
    return render_template('index.html', users = data, authorisation = authorisation, current = current_user, id = id, role = role)

#Авторизация
@app.route('/authorisation', methods=['GET', 'POST'])
def authorisation():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        checkbox = request.form.get('checkbox')
        userdata = Users.query.filter_by(username=username).first()

        if userdata and check_password_hash(userdata.password, password):
            login_user(userdata, remember=checkbox)
            flash(f"Вы успешно зарегестрировались на сайте!", "success")
            return redirect(url_for('index'))
        else:
            flash(f"Вы неправильно ввели данные, попробуйте ещё раз {password} {userdata.password} {check_password_hash(userdata.password, password)}", "danger")
            return redirect(url_for('authorisation'))

    return render_template('authorisation.html', title='Авторизация')



#Открывает страницу для изменения пароля текущего пользователя
@app.route('/change')
def change():
    return render_template('change.html')

#Выполняет функционал страницы для изменения пароля текущего пользователя
@app.route('/changed', methods=['POST'])
def changed():

    user_correct = 1
    password_correct = 1

    data = Users.query.all()

    if current_user.is_authenticated:
        authorisation = "user"
    else:
        authorisation = "anonymous"
    
    userdata = Users.query.get(current_user.id)
    password = userdata.password

    oldpassword = request.form.get('oldpassword')
    newpassword = request.form.get('newpassword')
    newpasswordagain = request.form.get('newpasswordagain')
    check = check_exam("qwerty", newpassword)
    if check == [1, 2]:
        user_correct = 1
        password_correct = 1
        if check_password_hash(userdata.password, oldpassword):
            if newpassword == newpasswordagain:
                password_correct = 1
                flash(f"Установлен новый пароль", "success")
                userdata.password = newpassword
                db.session.commit()
                return render_template('index.html', users = data, authorisation = authorisation)
            else:
                password_correct = 3 #Не совпадение новых паролей.
                flash(f"Пароли не совпадают.", "danger")
                return render_template('change.html', oldpassword=oldpassword, newpassword=newpassword, newpasswordagain=newpasswordagain, user_correct=user_correct, password_correct=password_correct)
        else:
            password_correct = 2 #Неправильный старый пароль.
            flash(f"Такой пароль не был установлен в системе. Введите старый пароль ещё раз.", "danger")
            return render_template('change.html', oldpassword=oldpassword, newpassword=newpassword, newpasswordagain=newpasswordagain, user_correct=user_correct, password_correct=password_correct)
    else:
        if 3 in check:
            flash(f"В логине могут быть только строчные и прописные буквы из латинского алфавита и цифры", "danger")
            user_correct = 0
        if 4 in check:
            flash(f"Длина логина должна быть не менее 5 символов", "danger")
            user_correct = 0
        if 5 in check:
            flash(f"Пароль не соответствует размеру", "danger")
            password_correct = 0
        if 6 in check:
            flash(f"В пароле введены неправильные символы", "danger")
            password_correct = 0
        if 7 in check:
            flash(f"В пароле должны быть 1 строчная буква, 1 прописная буква и 1 цифра", "danger")
            password_correct = 0
        return render_template('change.html', oldpassword=oldpassword, newpassword=newpassword, newpasswordagain=newpasswordagain, user_correct=user_correct, password_correct=password_correct)
            


def before_index():
    data = Users.query.all()
    if current_user.is_authenticated:
        authorisation = "user"
    else:
        authorisation = "anonymous"
    return render_template('index.html', users = data, authorisation = authorisation)

@app.route('/index', methods=['GET', 'POST'])
def index():
    data = Users.query.all()
    if current_user.is_authenticated == False:
        current_user.role = None
    return render_template('index.html', users = data, role = current_user.role, current_user=current_user)

#Выход из системы
@app.route('/goout', methods=['GET', 'POST'])
def goout():
    if request.method == 'POST':
        logout_user()
        flash("Вы вышли из системы, повторно пройдите автоизацию!", "success")
        return redirect(url_for('authorisation'))
    return render_template('authorisation.html', title='Авторизация')


@app.route('/record/<int:id>', methods=['GET'])
# @role_required("user", "admin")
@check_rights(["user", "admin"])
def record(id):
    data = Users.query.get(id)
    id = data.id
    username = data.username
    password = data.password
    name = data.name
    surname = data.surname
    patronymic = data.patronymic
    role = data.role
    date = data.date
    if current_user.role == "user":
        if current_user.id != id:
            flash(f"Это не ваша страничка, вы не можете её смотреть.", "danger")
            return before_index() #Возвращение на главную страницу (Запиши про return before_index() в конспекты)
        else:
            return render_template('record.html', id = id, username = username, password = password, name = name, surname = surname, patronymic = patronymic, role = role, date = date)
    else:
        return render_template('record.html', id = id, username = username, password = password, name = name, surname = surname, patronymic = patronymic, role = role, date = date)



@app.route('/create', methods=['GET', 'POST'])
@login_required
# @role_required("admin")
@check_rights(["admin"])
def create():
    user_correct = 1
    password_correct = 1
    
    if current_user.is_authenticated:
        authorisation = "user"
    else:
        authorisation = "anonymous"

    if request.method == 'POST':
        username = request.form.get('username')
        originalpassword = request.form.get('password')
        password = generate_password_hash(request.form.get('password'))
        name = request.form.get('name')
        surname = request.form.get('surname')
        patronymic = request.form.get('patronymic')
        role = request.form.get('role')
        now = datetime.now().date()

        check = check_exam(username, originalpassword)
        if check == [1, 2]:
            user_correct = 1
            password_correct = 1
            
            try:
                new_user = Users(
                    username = username, 
                    password = password, 
                    name = name, 
                    surname = surname, 
                    patronymic = patronymic, 
                    role = role, 
                    date = now
                )
                db.session.add(new_user)
                db.session.commit()
                flash("Успешно добавлена новая запись", "success")
                data = Users.query.all()
                return redirect(url_for('index'))
            except Exception as e:
                flash("Ошибка:" + str(e), "danger")
            return render_template('create.html', username=username, password=originalpassword, name=name, surname=surname, patronymic = patronymic, role = role)
        
        else: 
            if 3 in check:
                flash(f"В логине могут быть только строчные и прописные буквы из латинского алфавита и цифры", "danger")
                user_correct = 0
            if 4 in check:
                flash(f"Длина логина должна быть не менее 5 символов", "danger")
                user_correct = 0
            if 5 in check:
                flash(f"Пароль не соответствует размеру", "danger")
                password_correct = 0
            if 6 in check:
                flash(f"В пароле введены неправильные символы", "danger")
                password_correct = 0
            if 7 in check:
                flash(f"В пароле должны быть 1 строчная буква, 1 прописная буква и 1 цифра", "danger")
                password_correct = 0
            return render_template('create.html', username=username, password=originalpassword, name=name, surname=surname, patronymic = patronymic, role = role, user_correct = user_correct, password_correct = password_correct)

    return render_template('create.html')

#Обновление данных записи

@app.route('/editing/<int:id>', methods=['GET', 'POST'])
@login_required
# @role_required("user", "admin")
@check_rights(["admin", "user"])
def editing(id):

    data = Users.query.get(id)
    id = data.id
    username = data.username
    password = data.password
    name = data.name
    surname = data.surname
    patronymic = data.patronymic
    role = data.role
    date = data.date
    if current_user.role == "user":
        if current_user.id != id:
            flash(f"Это не ваша страничка, вы не можете её редактировать.", "danger")
            return before_index() #Возвращение на главную страницу (Запиши про return before_index() в конспекты)
        else:
            return render_template('record.html', id = id, username = username, password = password, name = name, surname = surname, patronymic = patronymic, role = role, date = date)
    else:
        return render_template('editing.html', user=data, id = id, username = username, password = password, name = name, surname = surname, patronymic = patronymic, role = role, date = date)

#Записываем полученные из формы данные (обновлённые) в БД
@app.route('/finalediting', methods=['GET', 'POST'])
def finalediting():
    if current_user.is_authenticated:
        authorisation = "user"
    else:
        authorisation = "anonymous"
    
    if request.method == "POST":
        id = request.form.get('id')
        data = Users.query.get(id)
        name = request.form.get('name')
        surname = request.form.get('surname')
        patronymic = request.form.get('patronymic')
        role = request.form.get('role')

        data.name = name
        data.surname = surname
        data.patronymic = patronymic
        data.role = role

        db.session.commit()
        flash(f"Пользователь {id} успешно обновлён")
        data = Users.query.all()
        return render_template('index.html', users = data, authorisation = authorisation)
    


#Модульное окно для удаления записи
@app.route('/delete/<int:id>', methods=['GET', 'POST'])
@check_rights(["admin"])
# @role_required("admin")
@login_required
def delete(id):
    if current_user.is_authenticated:
        authorisation = "user"
    else:
        authorisation = "anonymous"
    user = Users.query.get(id)
    if user is None:
        flash("Пользователь не найден", "danger")
        return redirect(url_for('index'))
    
    db.session.delete(user)
    db.session.commit()

    flash("Пользователь удалён", "success")
    data = Users.query.all()
    return render_template('index.html', users = data, authorisation = authorisation)

if __name__ == "__main__":
    app.run(debug=True)


