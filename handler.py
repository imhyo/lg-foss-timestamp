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
from apiclient.discovery import build
from google.appengine.ext import webapp
from oauth2client.appengine import OAuth2Decorator

import data_model
import dashboard
import settings
import user_auth

decorator = OAuth2Decorator(
	client_id=settings.CLIENT_ID,
	client_secret=settings.CLIENT_SECRET,
	scope=settings.SCOPE)

#service = build('calendar', 'v3')
service = build('tasks', 'v1')




JINJA_ENVIRONMENT = jinja2.Environment(
	loader = jinja2.FileSystemLoader(os.path.dirname(__file__)),
	extensions = ['jinja2.ext.autoescape'],
	autoescape = True)



	
# Returns the list of last 5 working history.
def getTimestamps():
	user = users.get_current_user()
	timestamps_query = data_model.Timestamp.query(
		ancestor = user_auth.get_user_key(user)).order(-data_model.Timestamp.start)
	return (timestamps_query.fetch(5))


# Handler for the main page
class MainPage(webapp2.RequestHandler):
	@user_auth.auth_required
	def get(self):
		timestamps = getTimestamps()
		# utc and kst are passed to the jinja2 framework, so that jinja can convert the UTC timestored in DB into the Asia/Seoul time.
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
	@user_auth.auth_required
	def post(self):
		user = users.get_current_user();
		timestamp = data_model.Timestamp(parent=get_user_key(user))
		timestamp.put()
		self.redirect('/')

		
class Checkout(webapp2.RequestHandler):
	@user_auth.auth_required
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
	@user_auth.auth_required
	def post(self):
		timestamps = getTimestamps()
		if len(timestamps) > 0:
			timestamp = timestamps[0]
			timestamp.key.delete()
		self.redirect('/')


		
class NoAuthority(webapp2.RequestHandler):
	def get(self):
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
