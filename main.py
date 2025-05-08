from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from dotenv import load_dotenv
import os
import requests


load_dotenv()

# UPDATE FORM
class UpdateForm(FlaskForm):
    rating = StringField('Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField('Review', validators=[DataRequired()])
    submit = SubmitField('Submit')


# ADD FORM
class AddForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


app = Flask(__name__)


app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
Bootstrap5(app)


# CREATE DB
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("SQLALCHEMY_DATABASE_URI")
db.init_app(app)


# MOVIE MODEL
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

    def __repr__(self):
        return f'<Movie {self.title}>'


# with app.app_context():
#     db.create_all()


# CREATE TABLE
# with app.app_context():
#     new_movie = Movie(
#         title="Phone Booth",
#         year=2002,
#         description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#         rating=7.3,
#         ranking=10,
#         review="My favourite character was the caller.",
#         img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
#     )
#
#     db.session.add(new_movie)
#     db.session.commit()
#
#     second_movie = Movie(
#         title="Avatar The Way of Water",
#         year=2022,
#         description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#         rating=7.3,
#         ranking=9,
#         review="I liked the water.",
#         img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
#     )
#     db.session.add(second_movie)
#     db.session.commit()


HEADERS = {
    "accept": "application/json",
    "Authorization": os.environ.get("TOKEN")
}


def get_movie_detail(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def get_movie(title, page):
    url = f"https://api.themoviedb.org/3/search/movie?query={title}&include_adult=false&language=en-US&page={page}"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()

    total_movies = len(all_movies)
    for index in range(total_movies):
        all_movies[index].ranking = total_movies - index

    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=['GET', 'POST'])
def edit():
    form = UpdateForm()
    movie_id = request.args.get('id')
    if form.validate_on_submit():
        movie_to_update = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()
        movie_to_update.rating = request.form['rating']
        movie_to_update.review = request.form['review']
        db.session.commit()
        return redirect(url_for('home'))

    movie = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()
    return render_template("edit.html", form=form, movie=movie)


@app.route('/delete')
def delete():
    movie_id = request.args.get('id')
    book_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(book_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=['GET', 'POST'])
def add():
    form = AddForm()
    if form.validate_on_submit():
        data = request.form
        movie_title = data['title']
        return redirect(url_for('select', page=1, title=movie_title))

    return render_template('add.html', form=form)


@app.route('/find')
def find():
    movie_api_id = request.args.get('id')
    response = get_movie_detail(movie_api_id)

    title = response['title']
    img_url = response['poster_path']
    year = response['release_date'].split('-')[0]
    description = response['overview']

    movie = Movie(
        title=title,
        year=year,
        description=description,
        img_url=f"https://image.tmdb.org/t/p/w500{img_url}"
    )
    db.session.add(movie)
    db.session.commit()

    return redirect(url_for('edit', id=movie.id))


@app.route('/select')
def select():
    title = request.args.get('title')
    page = request.args.get('page')
    response = get_movie(title, page)
    movies = response['results']
    return render_template('select.html', movies=movies, results=response['total_results'],
                           pages=response['total_pages'], title=title, current_page=page)


#
# @app.route('/add/<title>/page/<int:page>')
# def select(page, title):
#     response = get_movie(title, page)
#     movies = response['results']
#     return render_template('select.html', movies=movies, results=response['total_results'], pages=response['total_pages'], title=title, current_page=page)

if __name__ == '__main__':
    app.run(debug=True)
