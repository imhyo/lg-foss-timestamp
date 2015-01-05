import os
import cgi
import urllib
import datetime
import pytz

from pytz import timezone
from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2
import logging

from data_modules import Timestamp
from data_modules import User

JINJA_ENVIRONMENT = jinja2.Environment(
	loader = jinja2.FileSystemLoader(os.path.dirname(__file__)),
	extensions = ['jinja2.ext.autoescape'],
	autoescape = True)

# We set a parent key on the 'User' to ensure that they are all in the same
# entity group. Queries across the single entity group will be consistent.
def user_key(user):
	return ndb.Key('User', user.user_id())

def checkAuthority(self):
	nickname = users.get_current_user().nickname()
	user_key = ndb.Key('User', nickname)
	users_query = User(key = user_key).query()
	user = users_query.fetch(1)[0]
	if user.nickname != nickname:
		self.redirect("/no_authority")
	
def getTimestamps():
	user = users.get_current_user()
	timestamps_query = Timestamp.query(
		ancestor = user_key(user)).order(-Timestamp.start)
	return (timestamps_query.fetch(5))

	
class MainPage(webapp2.RequestHandler):
	def get(self):
		checkAuthority(self)
		timestamps = getTimestamps()
		utc = pytz.timezone('UTC')
		kst = pytz.timezone('Asia/Seoul')
		logout_url = users.create_logout_url(self.request.uri)
		
		template_values = {
			'timestamps': timestamps,
			'utc': utc,
			'kst': kst,
			'logout_url': logout_url,
		}
		
		template = JINJA_ENVIRONMENT.get_template('index.html')
		self.response.write(template.render(template_values))


class Checkin(webapp2.RequestHandler):
	def post(self):
		checkAuthority(self)
		user = users.get_current_user();
		timestamp = Timestamp(parent=user_key(user))
		timestamp.put()
		self.redirect('/')

		
class Checkout(webapp2.RequestHandler):
	def post(self):
		checkAuthority(self)
		timestamps = getTimestamps()
		if len(timestamps) > 0:
			timestamp = timestamps[0]
			timestamp.content = self.request.get('content')
			timestamp.finish = datetime.datetime.now()
			timestamp.user = users.get_current_user()
			timestamp.put()
		self.redirect('/')
		
		
class Cancel(webapp2.RequestHandler):
	def post(self):
		checkAuthority(self)
		timestamps = getTimestamps()
		if len(timestamps) > 0:
			timestamp = timestamps[0]
			timestamp.key.delete()
		self.redirect('/')
		
class NoAuthority(webapp2.RequestHandler):
	def get(self):
		logging.info(self.request.uri)
		logout_url = users.create_logout_url('/')
		
		template_values = {
			'logout_url': logout_url,
		}
		
		template = JINJA_ENVIRONMENT.get_template('no_authority.html')
		self.response.write(template.render(template_values))
				

application = webapp2.WSGIApplication([
    ('/', MainPage),
	('/checkin', Checkin),
	('/checkout', Checkout),
	('/cancel', Cancel),
	('/no_authority', NoAuthority),
], debug=True)
