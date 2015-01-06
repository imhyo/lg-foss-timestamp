import os
import cgi
import urllib
import datetime
import pytz
import httplib2
import jinja2
import webapp2
import logging

from pytz import timezone
from google.appengine.api import users
from google.appengine.ext import ndb
from data_modules import Timestamp
from data_modules import User


from apiclient.discovery import build
from google.appengine.ext import webapp
from oauth2client.appengine import OAuth2Decorator

decorator = OAuth2Decorator(
	client_id='1008598535710-rgfacejdi6pvjudk47lssfnp27lhbigc.apps.googleusercontent.com',
	client_secret='dbq5-MQ3rvDf6F5ZPs--ubzE',
#	scope='https://www.googleapis.com/auth/calendar')
	scope='https://www.googleapis.com/auth/tasks')

#service = build('calendar', 'v3')
service = build('tasks', 'v1')



JINJA_ENVIRONMENT = jinja2.Environment(
	loader = jinja2.FileSystemLoader(os.path.dirname(__file__)),
	extensions = ['jinja2.ext.autoescape'],
	autoescape = True)

# We set a parent key on the 'User' to ensure that they are all in the same
# entity group. Queries across the single entity group will be consistent.
def get_user_key(user):
	return ndb.Key('User', user.nickname())


def auth_required(handler):
	def check_login(self, *args, **kwargs):
		nickname = users.get_current_user().nickname()
		user_key = get_user_key(users.get_current_user())
		users_query = User(key = user_key).query()
		users_list = users_query.fetch(1)
		if (not users_list) or (users_list[0].nickname != nickname):
			self.redirect("/no_authority")
		else:
			return handler(self, *args, **kwargs)

	return check_login
	
	
def getTimestamps():
	user = users.get_current_user()
	timestamps_query = Timestamp.query(
		ancestor = get_user_key(user)).order(-Timestamp.start)
	return (timestamps_query.fetch(5))

	
class MainPage(webapp2.RequestHandler):
	@auth_required
	def get(self):
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
	@auth_required
	def post(self):
		user = users.get_current_user();
		timestamp = Timestamp(parent=get_user_key(user))
		timestamp.put()
		self.redirect('/')

		
class Checkout(webapp2.RequestHandler):
	@auth_required
	def post(self):
		timestamps = getTimestamps()
		if len(timestamps) > 0:
			timestamp = timestamps[0]
			timestamp.content = self.request.get('content')
			timestamp.finish = datetime.datetime.now()
			timestamp.user = users.get_current_user()
			timestamp.put()
		self.redirect('/')
		
		
class Cancel(webapp2.RequestHandler):
	@auth_required
	def post(self):
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
			
			
class Test(webapp2.RequestHandler):
	@decorator.oauth_required
	def get(self):
#		http = decorator.http()
#		request = service.events().list(calendarId='primary')
#		events = request.execute(http=http)
		tasks = service.tasks().list(tasklist='@default').execute(
			http=decorator.http())
		self.response.write('<html><body><ul>')
		for task in tasks['items']:
			self.response.write('<li>%s</li>' % task['title'])
		self.response.write('</ul></body><html>')

						

application = webapp2.WSGIApplication([
	('/', MainPage),
	('/checkin', Checkin),
	('/checkout', Checkout),
	('/cancel', Cancel),
	('/no_authority', NoAuthority),
	('/test', Test),
	(decorator.callback_path, decorator.callback_handler()),
], debug=True)
