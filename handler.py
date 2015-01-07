import os
import datetime
import pytz
import jinja2
import webapp2
import logging

from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import webapp

import data_model
import dashboard
import settings
import user_auth
import history


JINJA_ENVIRONMENT = jinja2.Environment(
	loader = jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'views')),
	extensions = ['jinja2.ext.autoescape'],
	autoescape = True)


# Handler for the main page
class MainPage(webapp2.RequestHandler):
	@user_auth.auth_required
	def get(self):
		timestamps = history.getHistory(num=5)
		# utc and kst are passed to the jinja2 framework, so that jinja can convert the UTC timestored in DB into the Asia/Seoul time.
		utc = pytz.timezone('UTC')
		kst = pytz.timezone('Asia/Seoul')
		
		template_values = {
			'timestamps': timestamps,
			'utc': utc,
			'kst': kst,
		}
		
		template = JINJA_ENVIRONMENT.get_template('index.html')
		self.response.write(template.render(template_values))


class Checkin(webapp2.RequestHandler):
	@user_auth.auth_required
	def post(self):
		user = users.get_current_user();
		timestamp = data_model.Timestamp(parent=user_auth.get_user_key(user))
		timestamp.put()
		self.redirect('/')


class Checkout(webapp2.RequestHandler):
	@user_auth.auth_required
	def post(self):
		timestamps = history.getHistory()
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
		timestamps = history.getHistory()
		if len(timestamps) > 0:
			timestamp = timestamps[0]
			timestamp.key.delete()
		self.redirect('/')


		
class NoAuthority(webapp2.RequestHandler):
	def get(self):
		template_values = {
			'message': 'You don\'t have permission to this site. Please ask the administrator.'
		}
		
		template = JINJA_ENVIRONMENT.get_template('error.html')
		self.response.write(template.render(template_values))
			
			
class Logout(webapp2.RequestHandler):
	def get(self):
		logout_url = users.create_logout_url('/')
		self.redirect(logout_url)

application = webapp2.WSGIApplication([
	('/', MainPage),
	('/checkin', Checkin),
	('/checkout', Checkout),
	('/cancel', Cancel),
	('/logout', Logout),
	('/no_authority', NoAuthority),
], debug=True)
