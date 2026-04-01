from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from models import db, Course, Category, User, Review
from tools import CoursesFilter, ImageSaver
from datetime import datetime
bp = Blueprint('courses', __name__, url_prefix='/courses')


#-----------------------------------------------
#Страница, на которой выполняется весь функционал, связанный с курсами.
#-----------------------------------------------


COURSE_PARAMS = [
    'author_id', 'name', 'category_id', 'short_desc', 'full_desc'
]

def params():
    return { p: request.form.get(p) or None for p in COURSE_PARAMS }

def search_params():
    return {
        'name': request.args.get('name'),
        'category_ids': [x for x in request.args.getlist('category_ids') if x],
    }

#Функция, которая переделывает отзывы под вид, в котором они будут отображаться на сайте.
def correct_reviews(reviews):
    users = db.session.execute(db.select(User)).scalars().all()

    final_review = [] #Итоговый список
    use_review = {} #Словарь, из которых состоит final_review

    for review in reviews:
        for user in users:
            if review.user_id == user.id:
                use_review["user_id"] = f"{user.first_name} {user.middle_name} {user.last_name}"
        if review.rating == 0:
            use_review["rating"] = "Ужасно"
        if review.rating == 1:
            use_review["rating"] = "Плохо"
        if review.rating == 2:
            use_review["rating"] = "Неудовлетворительно"
        if review.rating == 3:
            use_review["rating"] = "Удовлетворительно"
        if review.rating == 4:
            use_review["rating"] = "Хорошо"
        if review.rating == 5:
            use_review["rating"] = "Отлично"

        use_review["course_id"] = review.course_id
        use_review["created_at"] = review.created_at
        use_review["text"] = review.text

        final_review.append(use_review)
        use_review = {}
    
    return final_review


#Начальная страница в курсах
@bp.route('/')
def index():
    courses = CoursesFilter(**search_params()).perform()
    pagination = db.paginate(courses)
    courses = pagination.items
    categories = db.session.execute(db.select(Category)).scalars()
    return render_template('courses/index.html',
                           courses=courses,
                           categories=categories,
                           pagination=pagination,
                           search_params=search_params())

#А зачем нужен new?
@bp.route('/new')
@login_required
def new():
    reviews = db.session.execute(db.select(Review)).scalars().all()
    course = Course()
    categories = db.session.execute(db.select(Category)).scalars()
    users = db.session.execute(db.select(User)).scalars()
    return render_template('courses/new.html',
                           categories=categories,
                           users=users,
                           course=course,
                           reviews=reviews)

#Создание нового курса
@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    f = request.files.get('background_img')
    img = None
    course = Course()
    try:
        if f and f.filename:
            img = ImageSaver(f).save()

        image_id = img.id if img else None
        course = Course(**params(), background_image_id=image_id)
        db.session.add(course)
        db.session.commit()

        flash(f'Курс {course.name} был успешно добавлен!', 'success')

        return redirect(url_for('courses.index'))


    except IntegrityError as err:
        flash(f'Возникла ошибка при записи данных в БД. Проверьте корректность введённых данных. ({err})', 'danger')
        db.session.rollback()
        categories = db.session.execute(db.select(Category)).scalars()
        users = db.session.execute(db.select(User)).scalars()
        return render_template('courses/new.html',
                            categories=categories,
                            users=users,
                            course=course)

#Отображение курса с нужным id
@bp.route('/<int:course_id>', methods=['GET','POST'])
def show(course_id):
    course = db.get_or_404(Course, course_id)
    original_reviews = db.session.execute(db.select(Review).filter_by(course_id=course_id).order_by(Review.created_at.desc()).limit(5)).scalars().all()

    every_reviews = db.session.execute(db.select(Review).filter_by(course_id=course_id).order_by(Review.created_at.desc())).scalars().all()

    last_review = db.session.execute(db.select(Review).filter_by(course_id=course_id).order_by(Review.created_at.desc())).scalars().first()

    sent_review = 0 #Показывает, отправлялся ли отзыв от нынешнего пользователя или нет (0 - не отправлял, 1 - отправлял)

    #Проверка того, отправлял ли нынешний пользователь отзыв
    for review in every_reviews:
        if current_user.id == review.user_id:
            sent_review = 1


    reviews = correct_reviews(original_reviews)


    if request.method == "POST":
        user_id = current_user.id
        text = request.form.get("text")
        rating = request.form.get("rating")
        course_id = course_id
        review = Review(user_id=user_id, course_id=course_id, text=text, rating=rating)

        course.rating_sum = int(course.rating_sum) + int(rating)
        course.rating_num = int(course.rating_num) + 1

        db.session.add(review)
        db.session.commit()

        original_reviews = db.session.execute(db.select(Review).filter_by(course_id=course_id).order_by(Review.created_at.desc()).limit(5)).scalars().all()
        reviews = correct_reviews(original_reviews)

        return render_template('courses/show.html', course=course, reviews=reviews, sent_review=sent_review, last_review=last_review)


    return render_template('courses/show.html', course=course, reviews=reviews, sent_review=sent_review, last_review=last_review)



# @bp.route('/courses/<int:course_id>/reviews', methods=['GET', 'POST'])
# def all_reviews(course_id):
#     course = db.get_or_404(Course, course_id)
#     original_reviews = db.session.execute(db.select(Review).filter_by(course_id=course_id).order_by(Review.created_at.desc())).scalars().all()

#     page = request.args.get("page", 1, type=int)
#     per_page = 10

#     if request.method == "POST":

#         review_filter = request.form.get("review_filter")

#         if review_filter == "new":
#             original_reviews = db.session.execute(db.select(Review).filter_by(course_id=course_id).order_by(Review.created_at.desc())).scalars().all()
#         elif review_filter == "good":
#             original_reviews = db.session.execute(db.select(Review).filter_by(course_id=course_id).order_by(Review.rating.desc())).scalars().all()
#         elif review_filter == "bad":
#             original_reviews = db.session.execute(db.select(Review).filter_by(course_id=course_id).order_by(Review.rating)).scalars().all()

#         pagination = original_reviews.paginate(page=page, per_page=per_page, error_out=False)
#         original_reviews = pagination.items
        
#         reviews = correct_reviews(original_reviews)
#         return render_template('courses/all_reviews.html', course=course, reviews=reviews, pagination=pagination)
    
#     pagination = original_reviews.paginate(page=page, per_page=per_page, error_out=False)
#     original_reviews = pagination.items
        
#     reviews = correct_reviews(original_reviews)
    
#     return render_template('courses/all_reviews.html', course=course, reviews=reviews)

@bp.route('/courses/<int:course_id>/reviews', methods=['GET', 'POST'])
def all_reviews(course_id):
    course = db.get_or_404(Course, course_id)

    page = request.args.get("page", 1, type=int)
    per_page = 10
    review_filter = request.args.get("filter", "new")

    if request.method == "POST":
        session["review_filter"] = request.form.get("review_filter")
    
    review_filter = session.get("review_filter", "new")

    stmt = db.select(Review).filter_by(course_id=course_id)

    if review_filter == "new":
        stmt = stmt.order_by(Review.created_at.desc())
    elif review_filter == "good":
        stmt = stmt.order_by(Review.rating.desc())
    elif review_filter == "bad":
        stmt = stmt.order_by(Review.rating)

    # 🔑 пагинация
    stmt = stmt.limit(per_page).offset((page - 1) * per_page)

    original_reviews = db.session.execute(stmt).scalars().all()
    reviews = correct_reviews(original_reviews)

    # 🔢 считаем общее количество
    total = db.session.scalar(
        db.select(db.func.count()).select_from(Review).filter_by(course_id=course_id)
    )

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        'courses/all_reviews.html',
        course=course,
        reviews=reviews,
        page=page,
        total_pages=total_pages,
        review_filter=review_filter
    )











# @bp.route('/courses/<int:course_id>/reviews', methods=['GET', 'POST'])
# def all_reviews(course_id):
#     course = db.get_or_404(Course, course_id)
#     original_reviews = db.session.execute(db.select(Review).filter_by(course_id=course_id).order_by(Review.created_at.desc())).scalars().all()
#     reviews = correct_reviews(original_reviews)

#     if request.method == "POST":

#         review_filter = request.form.get("review_filter")

#         page = request.args.get("page", 1, type=int)
#         per_page = 10

#         query = Review.query.filter_by(course_id=course_id)

#         if review_filter == "new":
#             query = query.order_by(Review.created_at.desc())
#         elif review_filter == "good":
#             query = query.order_by(Review.rating.desc())
#         elif review_filter == "bad":
#             query = query.order_by(Review.rating)

#         pagination = query.paginate(page=page, per_page=per_page, error_out=False)
#         original_reviews = pagination.items
        
#         # if review_filter == "new":
#         #     original_reviews = db.session.execute(db.select(Review).filter_by(course_id=course_id).order_by(Review.created_at.desc())).scalars().all()
#         # elif review_filter == "good":
#         #     original_reviews = db.session.execute(db.select(Review).filter_by(course_id=course_id).order_by(Review.rating.desc())).scalars().all()
#         # elif review_filter == "bad":
#         #     original_reviews = db.session.execute(db.select(Review).filter_by(course_id=course_id).order_by(Review.rating)).scalars().all()
        
#         reviews = correct_reviews(original_reviews)
#         return render_template('courses/all_reviews.html', course=course, reviews=reviews)
    
#     return render_template('courses/all_reviews.html', course=course, reviews=reviews)








# @bp.route('/courses/<int:course_id>/reviews')
# def all_reviews(course_id):
#     course = db.get_or_404(Course, course_id)

#     page = request.args.get("page", 1, type=int)
#     per_page = 10
#     review_filter = request.args.get("filter", "new")

#     query_review = db.session.execute(db.select(Review).filter_by(course_id=course_id).order_by(Review.created_at.desc())).scalars().all()

#     if review_filter == "new":
#         query_review = db.session.execute(db.select(Review).filter_by(course_id=course_id).order_by(Review.created_at.desc())).scalars().all()
#     elif review_filter == "good":
#         query_review = db.session.execute(db.select(Review).filter_by(course_id=course_id).order_by(Review.rating.desc())).scalars().all()
#     elif review_filter == "bad":
#         query_review = db.session.execute(db.select(Review).filter_by(course_id=course_id).order_by(Review.rating)).scalars().all()

#     pagination = query_review.paginate(page=page, per_page=per_page, error_out=False)
#     original_reviews = pagination.items

#     reviews = correct_reviews(original_reviews)

#     return render_template(
#         'courses/all_reviews.html',
#         course=course,
#         reviews=reviews,
#         pagination=pagination,
#         review_filter=review_filter
#     )
