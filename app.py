#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for,jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
import sys
from datetime import datetime
# from config import app,db,moment,current_time, migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
current_time = datetime.now().strftime(('%Y-%m-%d %H:%M:%S'))

# TODO: connect to a local postgresql database
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

from models import *

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  # We have to model data like the dummy data, as the data is displayed grouped by state anc city.
  # We create new list data, containing all the data in the required format, and do the grouping by state and city 
  venues = Venue.query.all()
  data = []
  venue_state_city = ''
  upcoming = 0
  seen = {}
  for venue in venues:

    # We can use filter on shows as it has been dynamically loaded, which returns a query on which filter can be executed
    upcoming_shows = venue.shows.filter(Show.start_time > current_time).all()
    upcoming = len(upcoming_shows)

    # If the (city, state) pair is already seen, then we just append the venue to the venues list
    if venue.city+venue.state in seen:
      for v in data:
        if v["city"] == venue.city and v["state"] == venue.state:
          v["venues"].append({
            "id" : venue.id,
            "name" : venue.name,
            "num_upcoming_shows" : upcoming
          })
    
    # Else we mark the (city, state) pair as visited, and create a new entry in data
    else:
      seen[venue.city + venue.state] = True
      data.append({
        "city" : venue.city,
        "state" : venue.state,
        "venues" : [{
          "id" : venue.id,
          "name" : venue.name,
          "num_upcoming_shows" : upcoming
        }]
      })

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['GET'])
def search_venue_form():
  form = VenueSearchForm()
  return render_template('forms/search_venue.html', form=form)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  venue_name = request.form['name']
  venues = Venue.query.filter(Venue.name.ilike(f'%{venue_name}%')).all()
  count = len(venues)
  response = {}
  response["count"] = count
  for venue in venues:
    if "data" not in response:
      response["data"] = []
    venue_data = {}
    venue_data["id"] = venue.id 
    venue_data["name"] = venue.name
    upcoming_shows = venue.shows.filter(Show.start_time > current_time).all()
    num_upcoming_shows = len(upcoming_shows)
    venue_data["num_upcoming_shows"] = num_upcoming_shows
    response["data"].append(venue_data)


  return render_template('pages/search_venues.html', results=response, search_term=venue_name)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  
  data = Venue.query.get(venue_id)
  past_shows = data.shows.filter(Show.start_time <= current_time).all()
  past_show_count = len(past_shows)
  for show in past_shows:

    #image and name need to be display which are not available in the show table
    setattr(show, 'artist_image_link',show.artist.image_link)
    setattr(show, 'artist_name', show.artist.name)

  #attributes past_show_count and past_show need to be added as they are accessed in the view.
  setattr(data, 'past_show_count', past_show_count)
  setattr(data, 'past_shows', past_shows)
  
  upcoming_shows = data.shows.filter(Show.start_time > current_time).all()
  upcoming_show_count = len(upcoming_shows)

  for show in upcoming_shows:

    #image and name need to be display which are not available in the show table
    setattr(show, 'artist_image_link',show.artist.image_link)
    setattr(show, 'artist_name', show.artist.name)
  
  #attributes upcoming_show_count and upcoming_shows need to be added as they are accessed in the view.
  setattr(data, 'upcoming_show_count', upcoming_show_count)
  setattr(data, 'upcoming_shows', upcoming_shows)
  

  #data = list(filter(lambda d: d['id'] == venue_id, [data1, data2, data3]))[0]
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  error_msg = None
  try:
    venue_name = request.form['name']
    venue_city = request.form['city']
    venue_state = request.form['state']
    venue_address = request.form['address']
    venue_phone = request.form['phone']
    venue_fb = request.form['facebook_link']
    venue_genres = request.form.getlist('genres')
    venue_web = request.form['website']
    image_link = request.form['image_link']
    seeking_talent = request.form.get('seeking_talent', False)
    if seeking_talent == 'y':
      seeking_talent = True
    else:
      seeking_talent = False
    description = request.form.get('seeking_description', None)
    if description is None:
      description = "No description"
    
    venue = Venue(name=venue_name, city=venue_city, state=venue_state,image_link=image_link, genres=venue_genres,address= venue_address, phone=venue_phone, facebook_link=venue_fb, website=venue_web, seeking_talent=seeking_talent, seeking_description=description)
    db.session.add(venue)
    db.session.commit()
  except Exception as e:
    error = True
    error_msg = e
    db.session.rollback()
  finally:
    db.session.close()
  
  if error:
    # TODO: on unsuccessful db insert, flash an error instead.
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed due to.' + error_msg)
  else:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  
  return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/delete', methods=['DELETE','GET'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  error = False
  error_msg = ''
  try:
    venue = Venue.query.get(venue_id)
    venue_name = venue.name
    db.session.delete(venue)
    db.session.commit()
  except Exception as e:
    error = True
    error_msg = e
    db.session.rollback()
  finally:
    db.session.close()

  if error:
    flash('An error occurred during deletion. Venue ' +venue.name+ ' could not be deleted due to '+ error_msg)
  
  else:
  # on successful db insert, flash success
    flash('Venue ' + venue.name + ' was successfully deleted!')
  
  return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database

  data = Artist.query.all()
  
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['GET'])
def search_artist_form():
  form = ArtistSearchForm()
  return render_template('forms/search_artist.html', form=form)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  
  artist_name = request.form['name']
  artists = Artist.query.filter(Artist.name.ilike(f'%{artist_name}%')).all()
  count = len(artists)
  response = {}
  response["count"] = count
  for artist in artists:
    if "data" not in response:
      response["data"] = []
    artist_data = {}
    artist_data["id"] = artist.id 
    artist_data["name"] = artist.name
    upcoming_shows = artist.shows.filter(Show.start_time > current_time).all()
    num_upcoming_shows = len(upcoming_shows)
    artist_data["num_upcoming_shows"] = num_upcoming_shows
    response["data"].append(artist_data)

  

  return render_template('pages/search_artists.html', results=response, search_term=artist_name)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  
  data = Artist.query.get(artist_id)
  past_shows = data.shows.filter(Show.start_time <= current_time).all()
  past_show_count = len(past_shows)

  #attributes past_show_count and past_show need to be added as they are accessed in the view.
  setattr(data, 'past_show_count', past_show_count)
  setattr(data, 'past_shows', past_shows)

  for show in past_shows:

    #image and name need to be display which are not available in the show table
    setattr(show, 'venue_image_link',show.venue.image_link)
    setattr(show, 'venue_name', show.venue.name)
  
  upcoming_shows = data.shows.filter(Show.start_time > current_time).all()
  upcoming_show_count = len(upcoming_shows)

  for show in upcoming_shows:

    #image and name need to be display which are not available in the show table
    setattr(show, 'venue_image_link',show.venue.image_link)
    setattr(show, 'venue_name', show.venue.name)
  
  #attributes upcoming_show_count and upcoming_shows need to be added as they are accessed in the view.
  setattr(data, 'upcoming_show_count', upcoming_show_count)
  setattr(data, 'upcoming_shows', upcoming_shows)
  #data = list(filter(lambda d: d['id'] == artist_id, [data1, data2, data3]))[0]
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  
  # TODO: populate form with fields from artist with ID <artist_id>
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False
  error_msg = None
  try:
    artist = Artist.query.get(artist_id)
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.website = request.form['website']
    seeking_venue = request.form.get('seeking_venue', False)
    if seeking_venue == 'y':
      artist.seeking_venue = True
    else:
      artist.seeking_venue = False
    seeking_description = request.form.get("seeking_description", None)
    if seeking_description is None:
      seeking_description = "No description provided"
    artist.seeking_description = seeking_description
    db.session.add(artist)
    db.session.commit()
    
  except Exception as e:
    error = True
    error_msg = e
    print(sys.exc_info())
    db.session.rollback()
  
  finally:
    db.session.close()
  
  if error:
  # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.' +error_msg)
  
  else:
  # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  
  #return render_template('pages/home.html')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

  # TODO: populate form with values from venue with ID <venue_id>
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  venue = Venue.query.get(venue_id)
  error = False
  error_msg = None
  try:
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.facebook_link = request.form['facebook_link']
    venue.website = request.form['website']
    venue.image_link = request.form['image_link']
    seeking_talent = request.form.get('seeking_talent',False)
    if seeking_talent == 'y':
      venue.seeking_talent = True
    else:
      venue.seeking_talent = False
    seeking_description = request.form.get('seeking_description', None)
    if seeking_description is None:
      seeking_description = 'No description'
    venue.seeking_description = seeking_description
    db.session.add(venue)
    db.session.commit()
  except Exception as e:
    error = True
    error_msg = e
    db.session.rollback()
  finally:
    db.session.close()
  
  if error:
    # TODO: on unsuccessful db insert, flash an error instead.
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be updated due to '+error_msg)
  else:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  error_msg = None
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genre = request.form.getlist('genres')
    image = request.form['image_link']
    fb = request.form['facebook_link']
    website = request.form['website']
    seeking_venue = request.form.get('seeking_venue', False)
    venue_description = request.form.get('seeking_description', None)
    print(genre)
    if seeking_venue == 'y':
      seeking_venue = True
    else:
      seeking_venue = False
    if venue_description is None:
      venue_description = 'No description given'
    artist = Artist(name=name, city=city, state=state, phone=phone, genres=genre, facebook_link=fb, website=website, image_link=image, seeking_venue=seeking_venue, seeking_description=venue_description)
    db.session.add(artist)
    db.session.commit()
    
  except Exception as e:
    error = True
    error_msg = e
    print(sys.exc_info())
    db.session.rollback()
  
  finally:
    db.session.close()
  
  if error:
  # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed due to' + error_msg)
  
  else:
  # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = Show.query.all()
  #new attributes for the show object need to be created to be passed into the view
  for show in data:
    setattr(show, 'artist_image_link', show.artist.image_link)
    setattr(show, 'artist_name', show.artist.name)
    setattr(show, 'venue_name', show.venue.name)
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error = False
  error_msg = ''
  e = ''
  try:
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    artist_exist = Artist.query.get(artist_id)
    venue_exist = Venue.query.get(venue_id)
    start_time = request.form['start_time']
    
    #only if valid artist and venue are entered, a record should be created in the shows table.
    if artist_exist and venue_exist:
      show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
      db.session.add(show)
      db.session.commit()
    else:
      error = True
      if artist_exist is None and venue_exist is None:
        error_msg = 'Artist and Venue do not exist'
      elif artist_exist is None:
        error_msg = 'Artist does not exist'
      elif venue_exist is None:
        error_msg = 'Venue does not exist'
    
  except Exception as e:
    error = True
    error_msg = e
    db.session.rollback()
  finally:
    db.session.close()
  
  if error:
    # TODO: on unsuccessful db insert, flash an error instead.
    flash(f'An error occurred. Show could not be listed.Error : {error_msg}')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  else:

    # on successful db insert, flash success
    flash('Show was successfully listed!')
  
  return render_template('pages/home.html')

@app.route('/shows/search', methods=['GET'])
def search_show_form():
  form = ShowSearchForm()
  return render_template('forms/search_show.html', form=form)

@app.route('/shows/search', methods=['POST'])
def search_shows():
  
  #search by artist_id and venue_id
  artist_id = request.form.get('artist_id', None)
  venue_id = request.form.get('venue_id', None)
  
  #if both are not entered return
  if artist_id == '' and venue_id == '':
      flash("Please Enter atleast 1 value")
      return redirect(url_for('search_shows'))

  #if both are entered, query shows using the and operator
  if artist_id != '' and venue_id != '':
    shows = Show.query.filter(Show.artist_id==artist_id, Show.venue_id == venue_id).all()
  else:
    #if any one is entered get a show with venue/artist_id equal to the entered value
    if artist_id == '':
      shows = Show.query.filter(Show.venue_id == venue_id).all()
    elif venue_id == '':
      shows = Show.query.filter(Show.artist_id==artist_id).all()
    
  #convert data into the required format to be passed to the view
  count = len(shows)
  response = {}
  response["count"] = count
  for show in shows:
    if "data" not in response:
      response["data"] = []
    show_data = {}
    show_data["artist_id"] = show.artist_id 
    show_data["venue_id"] = show.venue_id
    show_data["start_time"] = show.start_time
    show_data["artist_image_link"] = show.artist.image_link
    show_data["artist_name"] = show.artist.name
    show_data["venue_name"] = show.venue.name
    response["data"].append(show_data)


  return render_template('pages/search_shows.html', results=response, search_term_1=artist_id, search_term_2=venue_id)
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run(debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
