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

from data_modules import User

JINJA_ENVIRONMENT = jinja2.Environment(
	loader = jinja2.FileSystemLoader(os.path.dirname(__file__)),
	extensions = ['jinja2.ext.autoescape'],
	autoescape = True)

def getUsers():
	users_query = User.query()
	return (users_query.fetch())

	
class MainPage(webapp2.RequestHandler):
	def get(self):
		users = getUsers()
		template_values = {
			'users': users,
		}
		template = JINJA_ENVIRONMENT.get_template('admin.html')
		self.response.write(template.render(template_values))

		
class AddUser(webapp2.RequestHandler):
	def post(self):
		nickname = self.request.get('nickname')
		user_key = ndb.Key('User', nickname)
		user = User(key = user_key)
		user.nickname = nickname
		user.put()
		self.redirect('/admin/')
		

application = webapp2.WSGIApplication([
    ('/admin/', MainPage),
    ('/admin/add_user', AddUser),
], debug=True)
