import random
from flask import Flask, render_template, request
from faker import Faker

fake = Faker()

app = Flask(__name__)
application = app

images_ids = ['7d4e9175-95ea-4c5f-8be5-92a6b708bb3c',
              '2d2ab7df-cdbc-48a8-a936-35bba702def5',
              '6e12f3de-d5fd-4ebb-855b-8cbc485278b7',
              'afc2cfe7-5cac-4b80-9b9a-d5c65ef0c728',
              'cab5b7f2-774e-4884-a200-0c0180fa777f']

def generate_comments(replies=True):
    comments = []
    for i in range(random.randint(1, 3)):
        comment = { 'author': fake.name(), 'text': fake.text() }
        if replies:
            comment['replies'] = generate_comments(replies=False)
        comments.append(comment)
    return comments

def generate_post(i):
    return {
        'title': 'Заголовок поста',
        'text': fake.paragraph(nb_sentences=100),
        'author': fake.name(),
        'date': fake.date_time_between(start_date='-2y', end_date='now'),
        'image_id': f'{images_ids[i]}.jpg',
        'comments': generate_comments()
    }



#Функция обработки номеров телефона
def elite(phone):
    alphabet=["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"] #Алфавит цифр
    dopalphabet=[" ", "(", ")", "-", ".", "+"] #Дополнительный алфавит с знаками 
    alpha = [] #C len это кол-во символов из алфавита цифр
    dop = [] #С len это кол-во символов из дополнительного алфавита
    for i in phone:
        if i in alphabet:
            alpha.append(i)
        elif i in dopalphabet:
            dop.append(i)
        else:
            return 1
    if len(alpha) == 10:
        return 0
    elif len(alpha) == 11:
        if alpha[0] == "8" or (dop and dop[0] == "+" and alpha[0] == "7"):
            return 0
        else:
            return 2
    else:
        return 2




posts_list = sorted([generate_post(i) for i in range(5)], key=lambda p: p['date'], reverse=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/posts')
def posts():
    return render_template('posts.html', title='Посты', posts=posts_list)

@app.route('/posts/<int:index>')
def post(index):
    p = posts_list[index]
    return render_template('post.html', title=p['title'], post=p)

@app.route('/about')
def about():
    return render_template('about.html', title='Об авторе')

@app.route('/form', methods=["GET", "POST"])
def form():
    pamURL=None
    Kukies=None
    zagolovki=None
    pamform=None
    result="Not sent"
    resik=0 #Отвечает за цветовое отображение HTML-страниц, 'ok' - нет ошибки, "fail" - есть ошибка
    phone="Not sent"
    if request.method == "GET":
        phone=request.args.get("phone1")
        pamURL=request.args
        if phone:
            resik = elite(phone)
            if resik == 0:
                result = f"Проверка успешно завершена. Телефон подходит под формат"
            if resik == 1:
                result = f"Недопустимый ввод. В номере телефона встречаются недопустимые символы."
            if resik == 2:
                result = f"Недопустимый ввод. Неверное количество цифр."
        else:
            result="Not sent"
    elif request.method == "POST":
        phone=request.form.get("phone1")
        Kukies=request.cookies
        zagolovki=request.headers
        pamform=request.form
        if phone:
            result = elite(phone)
            if resik == 0:
                result = f"Проверка успешно завершена. Телефон подходит под формат"
            if resik == 1:
                result = f"Недопустимый ввод. В номере телефона встречаются недопустимые символы."
            if resik == 2:
                result = f"Недопустимый ввод. Неверное количество цифр."
        else:
            result="Not sent"

    else:
        result="Not sent"
        phone="Not sent"
        pamURL=None
        Kukies=None
        zagolovki=None
        pamform=None
        resik=0


    return render_template('form.html', title='Форма', phone=phone, zagolovki=zagolovki, Kukies=Kukies, pamURL=pamURL, pamform=pamform, result=result, resik=resik)

if __name__ == "__main__":
    app.run(debug=True)



# {% extends 'base.html' %}

# {% block content %}
# <div class="container-fluid">
#     <div class="row justify-content-center">
#         <div class = "col-md-8 mb-3 justify-content-start">

#             <div class="{% if rezik == 'fail' %} invalid-feedback d-block {% else %} d-block {% endif %}">
#                 <form class="card" action="/form" method="POST">
#                     <div class="card-header">
#                         <label for="input" class="form-label ms-2" aria-describedby="emailHelp">GET-форма</label>
#                     </div>
#                     <div class="card-text">
#                         <label for="phone_number" class="form-label ms-4 {% if rezik == 'fail' %} is-invalid {% endif %}" aria-describedby="emailHelp">Введите номер телефона</label>
#                         <input id="phone_number" class="form-control m-2 {% if rezik == 'fail' %} is-invalid {% endif %}" name="phone1" type="phone" style="width: calc(100% - 15px);" placeholder="Вот здесь">

#                         <textarea id="input" class="form-control m-2 {% if rezik == 'fail' %} is-invalid {% endif %}" style="width: calc(100% - 15px);" rows="4" placeholder="Введите комментарий: " ></textarea>
#                         <button type="submit" class="btn btn-primary m-2">Проверить</button>
#                     </div>
#                 </form>
#             </div>
#             <div>
#                 <p>
#                     Параметры URL-адреса: {{ pamURL }}<br><br>
#                     Статус обработки телефона: {{ result }}<br><br>
#                     Номер телефона: {{ phone }}<br><br>
#                 </p>
#             </div>

#             <div class="{% if rezik == 'fail' %} invalid-feedback d-block {% else %} d-block {% endif %}">
#                 <form class="card" action="/form" method="POST">
#                     <div class="card-header">
#                         <label for="input" class="form-label ms-2 {% if rezik == 'fail' %} is-invalid {% endif %}" aria-describedby="emailHelp">POST-форма</label>
#                     </div>
#                     <div class="card-text">
#                         <label for="phone_number1" class="form-label ms-4 {% if rezik == 'fail' %} is-invalid {% endif %}" aria-describedby="emailHelp">Введите номер телефона</label>
#                         <input id="phone_number1" class="form-control m-2 {% if rezik == 'fail' %} is-invalid {% endif %}" name="phone1" type="phone" style="width: calc(100% - 15px);" placeholder="Вот здесь">

#                         <textarea id="input1" class="form-control m-2 {% if rezik == 'fail' %} is-invalid {% endif %}" style="width: calc(100% - 15px);" rows="4" placeholder="Введите комментарий: " ></textarea>
#                         <button type="submit" class="btn btn-primary m-2">Проверить</button>
#                     </div>
#                 </form>
#             </div>
#             <div>
#                 <p>
#                     Заголовки запроса: {{ zagolovki }}<br><br>
#                     Файлы Cookies: {{ Kukies }}<br><br>
#                     Параметры формы: {{ pamform }}<br><br>
#                     Статус обработки телефона: {{ result }}<br><br>
#                     Номер телефона: {{ phone }}<br><br>
#                 </p>
#             </div>

#         </div>
#     </div>
# </div>    
# {% endblock %}