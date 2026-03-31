from flask import Flask, current_app, Blueprint, g, render_template, request, session, redirect, url_for, flash, get_flashed_messages, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from io import StringIO, BytesIO
from datetime import datetime
from functools import wraps
from models import db
from models import Users
from models import visit_logs
import csv

visitor = Blueprint('visitor', __name__, template_folder='templates', static_folder='static')

DATABASE = "lab5.db"

#Функция подключения БД во время запроса.
def get_db():
	if "db" not in g: #Если БД не подключена во время запроса, то происходит её подключение.
		g.db = db
	return g.db

#Функция, которая из списка с различными числами делает словарь, где напротив ключа-числа стоит значение количества появления числа в списке.
def count_numbers(lst):
    result = {}
    
    for num in lst:
        result[num] = result.get(num, 0) + 1
    
    return result
	


#Функция из страницы с отчётом по пользователям и их количеству посещений страниц
def func_report_users():
	logs = visit_logs.query.all()
	users = Users.query.all()
	unique_users = db.session.query(visit_logs.user_id).distinct().all()

	all_users = [] #Словарь с id пользователей и кол-во их посещений страниц

	for i in range(0, len(unique_users)):
		for log in logs:
			if log.user_id == unique_users[i].user_id:
				all_users.append(unique_users[i].user_id)
	
	all_users = count_numbers(all_users)

	all_logs = [] #Итоговый список со всеми пользователями, текстом и их количеством посещений

	if all_users:
		for log, count in all_users.items():
			if log == None:
				all_logs.append([f"Неаутентифицированный пользователь", count])
		for user in users:
			for log, count in all_users.items():
				if log == user.id:
					all_logs.append([f"{user.surname} {user.name} {user.patronymic}", count])

	all_logs.sort(key=lambda x: x[1], reverse=True)

	return all_logs

#Функция из страницы с отчётом по страницам и их посещениям
def func_report_pages():
	logs = visit_logs.query.all()

	count_index = 0 #Главная страница
	count_authorisation = 0 #Страница авторизации
	count_pages = 0 #Страница с отчётом по страницам
	count_users = 0 #Страница с отчётом по пользователям
	count_create = 0 #Страница с созданием записи пользователя
	count_change = 0 #Страница с изменением пароля

	record = [] #Просмотр записей
	editing = [] #Редактирование записей

	for log in logs:
		if log.path == "http://127.0.0.1:5000/" or log.path == "http://127.0.0.1:5000/index":
			count_index += 1
			# log.path == "Главная страница"
		elif "authorisation" in log.path:
			count_authorisation += 1
			# log.path == "Страница авторизации"
		elif "report_pages" in log.path:
			count_pages += 1
			# log.path == "Страница с отчётом по страницам"
		elif "report_users" in log.path:
			count_users += 1
			# log.created_at == "Страница с отчётом по пользователям"
		elif "create" in log.path:
			count_create += 1
			# log.created_at == "Страница с созданием записи пользователя"
		elif "change" in log.path:
			count_change += 1
			# log.created_at == "Страница с изменением пароля"
		elif "record" in log.path:
			url = log.path
			url = url.split('/')[-1]
			# count_record += 1
			record.append(url)
			
			log.created_at == f"Просмотр записи пользователя с id {log.user_id}"
		elif "editing" in log.path:
			url = log.path
			url = url.split('/')[-1]
			# count_record += 1
			editing.append(url)
			log.path == f"Редактирование записи пользователя с id {log.user_id}"
	
	records = count_numbers(record)
	editings = count_numbers(editing)

	all_visits = [] #Все записи зарегестрированных пользователей

	all_visits.append(["Главная страница", count_index])
	all_visits.append(["Страница авторизации", count_authorisation])
	all_visits.append(["Страница с отчётом по страницам", count_pages])
	all_visits.append(["Страница с отчётом по пользователям", count_users])
	all_visits.append(["Страница с созданием записи пользователя", count_create])
	all_visits.append(["Страница с изменением пароля", count_change])
	if records:
		for log, count in records.items():
			all_visits.append([f"Просмотр записи пользователя с id {log}", count])
	if editings:
		for log, count in editings.items():
			all_visits.append([f"Редактирование записи пользователя с id {log}", count])

	all_visits.sort(key=lambda x: x[1], reverse=True)

	return all_visits

@visitor.route("/anarchia")
def index():
	result = visit_logs.query.all()
	return "result"

@visitor.route("/visitor_log")
def visitor_log():
	data = Users.query.all()

	page = request.args.get('page', 1,type=int) #Текущая страница

	per_page = 20

	if current_user.is_authenticated == False:
		current_user.role = None
	else:
		if current_user.role == "user":
			logs = visit_logs.query.filter(
				visit_logs.user_id == current_user.id
				).order_by(
				visit_logs.created_at.desc()
				).all()
			pagination = visit_logs.query.filter(visit_logs.user_id == current_user.id).order_by(visit_logs.created_at.desc()).paginate(
				page = page,
				per_page = per_page,
				error_out = False
			)
		elif current_user.role == "admin":
			logs = visit_logs.query.order_by(visit_logs.created_at.desc()).all()
			pagination = visit_logs.query.order_by(visit_logs.created_at.desc()).paginate(
				page = page,
				per_page = per_page,
				error_out = False
			)
	
	page_users = pagination.items

	return render_template("visitor_log.html", page=page, page_users=page_users, pagination = pagination, visit_logs = logs, users = data, role = current_user.role, current_user = current_user)

#Страница с отчётом по страницам и их посещениям
@visitor.route("/report_pages")
def report_pages():
	logs = visit_logs.query.all()

	count_index = 0 #Главная страница
	count_authorisation = 0 #Страница авторизации
	count_pages = 0 #Страница с отчётом по страницам
	count_users = 0 #Страница с отчётом по пользователям
	count_create = 0 #Страница с созданием записи пользователя
	count_change = 0 #Страница с изменением пароля

	record = [] #Просмотр записей
	editing = [] #Редактирование записей

	for log in logs:
		if log.path == "http://127.0.0.1:5000/" or log.path == "http://127.0.0.1:5000/index":
			count_index += 1
			# log.path == "Главная страница"
		elif "authorisation" in log.path:
			count_authorisation += 1
			# log.path == "Страница авторизации"
		elif "report_pages" in log.path:
			count_pages += 1
			# log.path == "Страница с отчётом по страницам"
		elif "report_users" in log.path:
			count_users += 1
			# log.created_at == "Страница с отчётом по пользователям"
		elif "create" in log.path:
			count_create += 1
			# log.created_at == "Страница с созданием записи пользователя"
		elif "change" in log.path:
			count_change += 1
			# log.created_at == "Страница с изменением пароля"
		elif "record" in log.path:
			url = log.path
			url = url.split('/')[-1]
			# count_record += 1
			record.append(url)
			
			log.created_at == f"Просмотр записи пользователя с id {log.user_id}"
		elif "editing" in log.path:
			url = log.path
			url = url.split('/')[-1]
			# count_record += 1
			editing.append(url)
			log.path == f"Редактирование записи пользователя с id {log.user_id}"
	
	records = count_numbers(record)
	editings = count_numbers(editing)

	all_visits = [] #Все записи зарегестрированных пользователей

	all_visits.append(["Главная страница", count_index])
	all_visits.append(["Страница авторизации", count_authorisation])
	# all_visits.append(["Страница с отчётом по страницам", count_pages])
	# all_visits.append(["Страница с отчётом по пользователям", count_users])
	all_visits.append(["Страница с созданием записи пользователя", count_create])
	all_visits.append(["Страница с изменением пароля", count_change])
	if records:
		for log, count in records.items():
			all_visits.append([f"Просмотр записи пользователя с id {log}", count])
	if editings:
		for log, count in editings.items():
			all_visits.append([f"Редактирование записи пользователя с id {log}", count])

	all_visits.sort(key=lambda x: x[1], reverse=True)

	return render_template("report_pages.html", all_visits = all_visits)

#Страница с отчётом по пользователям и их количеству посещений страниц
@visitor.route("/report_users")
def report_users():
	logs = visit_logs.query.all()
	users = Users.query.all()
	unique_users = db.session.query(visit_logs.user_id).distinct().all()

	all_users = [] #Словарь с id пользователей и кол-во их посещений страниц

	for i in range(0, len(unique_users)):
		for log in logs:
			if log.user_id == unique_users[i].user_id:
				all_users.append(unique_users[i].user_id)
	
	all_users = count_numbers(all_users)

	all_logs = [] #Итоговый список со всеми пользователями, текстом и их количеством посещений

	if all_users:
		for log, count in all_users.items():
			if log == None:
				all_logs.append([f"Неаутентифицированный пользователь", count])
		for user in users:
			for log, count in all_users.items():
				if log == user.id:
					all_logs.append([f"{user.surname} {user.name} {user.patronymic}", count])

	all_logs.sort(key=lambda x: x[1], reverse=True)

	return render_template("report_users.html", all_logs = all_logs )

@visitor.route("/export_pages_csv")
def export_pages_csv():
    all_visits = func_report_pages()

    si = StringIO()
    writer = csv.writer(si)

    # Заголовки
    writer.writerow(["№", "Страница", "Количество посещений"])

    # Данные
    for i, visit in enumerate(all_visits, start=1):
        writer.writerow([i, visit[0], visit[1]])

    # Перевод в байты
    mem = BytesIO()
    mem.write(si.getvalue().encode('utf-8-sig'))  # 👈 важно для Excel
    mem.seek(0)

    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name='pages_report.csv'
    )

@visitor.route('/export_users_csv')
def export_users_csv():
    all_logs = func_report_users()

    si = StringIO()
    writer = csv.writer(si)

    # Заголовки
    writer.writerow(["№", "Пользователь", "Количество посещений"])

    # Данные
    for i, log in enumerate(all_logs, start=1):
        writer.writerow([i, log[0], log[1]])

    # Перевод в байты (важно для скачивания)
    mem = BytesIO()
    mem.write(si.getvalue().encode('utf-8-sig'))  # 👈 чтобы Excel открывал нормально
    mem.seek(0)

    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name='users_report.csv'
    )