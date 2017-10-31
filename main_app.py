# An application about recording favorite songs & info

# 1:Many relationship: Album:Song(s)
# Many:Many relationship: Artists:Songs
# TODO: E-R diagram to display
# TODO: relationship to build (done, ish)
# TODO: relationship and association table to build

import os
from flask import Flask, render_template, session, redirect, url_for, flash
from flask_script import Manager, Shell
# from flask_moment import Moment # requires pip/pip3 install flask_moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy
# from flask_sqlalchemy import Table, Column, Integer, ForeignKey, String, DateTime, Date, Time
# from flask_sqlalchemy import relationship, backref

from flask_migrate import Migrate, MigrateCommand # needs: pip/pip3 install flask-migrate

# Configure base directory of app
basedir = os.path.abspath(os.path.dirname(__file__))

# Application configurations
app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'hardtoguessstringfromsi364thisisnotsupersecurebutitsok'
# app.config['SQLALCHEMY_DATABASE_URI'] =\
    # 'sqlite:///' + os.path.join(basedir, 'data.sqlite') # Determining where your database file will be stored, and what it will be called
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/songs_data"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Set up Flask debug stuff
manager = Manager(app)
# moment = Moment(app) # For time # Later
db = SQLAlchemy(app) # For database use
migrate = Migrate(app, db) # For database use/updating
manager.add_command('db', MigrateCommand) # Add migrate command to manager

## Set up Shell context so it's easy to use the shell to debug
# Define function
def make_shell_context():
    return dict( app=app, db=db, Song=Song, Artist=Artist)
# Add function use to manager
manager.add_command("shell", Shell(make_context=make_shell_context))

## You will get the following message when running command to create migration folder:
## python main_app.py db init
## -->
# Please edit configuration/connection/logging settings in ' ... migrations/alembic.ini' before proceeding
## This is what you are supposed to see!

#########
######### Everything above this line is important/useful setup, not problem-solving.
#########

##### Set up Models #####

# Set up association Table
collections = db.Table('collections',db.Column('album_id',db.Integer, db.ForeignKey('Album.id')),db.Column('artist_id',db.Integer, db.ForeignKey('Artist.id')))

class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    artists = db.relationship('Artist',secondary=collections,backref=db.backref('albums',lazy='dynamic'),lazy='dynamic')

class Artist(db.Model):
    __tablename__ = "artists"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    songs = db.relationship('Song',backref='Artist')

    def __repr__(self):
        return "{} (ID: {})".format(self.name,self.id)

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64),unique=True) # Only unique title songs
    artist_id = db.Column(db.Integer, db.ForeignKey("artists.id")) # changed
    genre = db.Column(db.String(64))

    def __repr__(self):
        return "{} by {} | {}".format(self.title,self.artist, self.genre)



##### Set up Forms #####

class SongForm(FlaskForm):
    song = StringField("What is the title of your favorite song?", validators=[Required()])
    artist = StringField("What is the name of the artist who performs it?",validators=[Required()])
    genre = StringField("What is the genre of that song?", validators
        =[Required()])
    submit = SubmitField('Submit')

##### Helper functions

### For database additions / get_or_create functions

def get_or_create_artist(db_session,artist_name):
    artist = db_session.query(Artist).filter_by(name=artist_name).first()
    if artist:
        return artist
    else:
        artist = Artist(name=artist_name)
        db_session.add(artist)
        db_session.commit()
        return artist

def get_or_create_song(db_session, song_title, song_artist, song_genre):
    song = db_session.query(Song).filter_by(title=song_title).first()
    if song:
        return song
    else:
        artist = get_or_create_artist(db_session, song_artist)
        song = Song(title=song_title,genre=song_genre,artist_id=artist.id)
        db_session.add(song)
        db_session.commit()
        return song




##### Set up Controllers (view functions) #####

## Error handling routes
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

## Main route

@app.route('/', methods=['GET', 'POST'])
def index():
    songs = Song.query.all()
    num_songs = len(songs)
    form = SongForm()
    if form.validate_on_submit():
        if db.session.query(Song).filter_by(title=form.song.data).first(): # If there's already a song with that title, though...
            flash("You've already saved a song with that title!")
        get_or_create_song(db.session,form.song.data, form.artist.data, form.genre.data)
        return redirect(url_for('see_all'))
    return render_template('index.html', form=form,num_songs=num_songs)

@app.route('/all_songs')
def see_all():
    all_songs = [] # To be tuple list of title, genre
    songs = Song.query.all()
    for s in songs:
        artist = Artist.query.filter_by(id=s.artist_id).first()
        all_songs.append((s.title,artist.name, s.genre))
    return render_template('all_songs.html',all_songs=all_songs)

@app.route('/all_artists')
def see_all_artists():
    artists = Artist.query.all()
    names = [(a.name, len(Song.query.filter_by(artist_id=a.id).all())) for a in artists]
    return render_template('all_artists.html',artist_names=names)

if __name__ == '__main__':
    db.create_all()
    manager.run() # NEW: run with this: python main_app.py runserver
    # Also provides more tools for debugging
