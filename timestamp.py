import os
import cgi
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
	loader = jinja2.FileSystemLoader(os.path.dirname(__file__)),
	extensions = ['jinja2.ext.autoescape'],
	autoescape = True)

# We set a parent key on the 'Username' to ensure that they are all in the same
# entity group. Queries across the single entity group will be consistent.
# However, the write rate should be limited to ~1/second.

def user_key(user):
	return ndb.Key('Username', user.user_id())
	
class Timestamp(ndb.Model):
	"""Models an individual Timestamp entry."""
	start = ndb.DateTimeProperty(auto_now_add=True)
	finish = ndb.DateTimeProperty(auto_now_add=False)
	content = ndb.StringProperty(indexed=False)

class MainPage(webapp2.RequestHandler):
    def get(self):
		user = users.get_current_user()
		
		timestamps_query = Timestamp.query(
			ancestor = user_key(user)).order(-Timestamp.start)
		timestamps = timestamps_query.fetch(5)
		
		template_values = {
			'timestamps': timestamps,
		}
		
		template = JINJA_ENVIRONMENT.get_template('index.html')
		self.response.write(template.render(template_values))


class Checkin(webapp2.RequestHandler):
	def post(self):
		user = users.get_current_user();
		timestamp = Timestamp(parent=user_key(user))
		timestamp.put()
		self.redirect('/')

application = webapp2.WSGIApplication([
    ('/', MainPage),
	('/checkin', Checkin),
], debug=True)
