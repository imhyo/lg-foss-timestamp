import os
import datetime
import pytz
import httplib2
import jinja2
import webapp2
import logging

from google.appengine.api import users
from google.appengine.ext import webapp

import data_model
import user_auth
import history


JINJA_ENVIRONMENT = jinja2.Environment(
	loader = jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'views')),
	extensions = ['jinja2.ext.autoescape'],
	autoescape = True)


# Handler for the main page
class ShowHistory(webapp2.RequestHandler):
	@user_auth.auth_required
	def get(self):
		min_str = self.request.get('min')
		max_str = self.request.get('max')
		num_str = self.request.get('num')
		min = None
		max = None
		num = 0
		logging.info (min_str + " " + max_str + " " + num_str)
		if min_str and min_str is not '':
			min = datetime.date(int(min_str[0:4]), int(min_str[4:6]), int(min_str[6:8]))
		if max_str and max_str is not '':
			max = datetime.date(int(max_str[0:4]), int(max_str[4:6]), int(max_str[6:8]))
		if num_str:
			num = int(num_str)
		
		timestamps = history.getHistory(min=min, max=max, num=num)
		# utc and kst are passed to the jinja2 framework, so that jinja can convert the UTC timestored in DB into the Asia/Seoul time.
		utc = pytz.timezone('UTC')
		kst = pytz.timezone('Asia/Seoul')
		
		template_values = {
			'timestamps': timestamps,
			'utc': utc,
			'kst': kst,
		}
		
		template = JINJA_ENVIRONMENT.get_template('show_history.html')
		self.response.write(template.render(template_values))


application = webapp2.WSGIApplication([
	('/show_history', ShowHistory),
], debug=True)
