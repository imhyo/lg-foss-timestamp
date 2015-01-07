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

import settings
import user_auth


JINJA_ENVIRONMENT = jinja2.Environment(
	loader = jinja2.FileSystemLoader(os.path.dirname(__file__)),
	extensions = ['jinja2.ext.autoescape'],
	autoescape = True)

decorator = OAuth2Decorator(
	client_id=settings.CLIENT_ID,
	client_secret=settings.CLIENT_SECRET,
	scope=settings.SCOPE)

service = build('calendar', 'v3')


class Dashboard(webapp2.RequestHandler):
	@user_auth.auth_required
	def get(self):
		user = users.get_current_user()
		year_str = self.request.get('year')
		if (not year_str):
			year = datetime.date.today().year
		else:
			year = int(year_str)
		self.showDashboard(user.nickname(), year)


	def getWeeks(self, nickname, year):
		h = self.getHolidays(nickname, year)
		weeks = range(54)
		one_day = datetime.timedelta(1)
		date = datetime.date(year, 1, 1)
		end_date = datetime.date(year, 12, 31)
		for i in range(54):
			weeks[i] = [datetime.date(year, 1, 1), datetime.date(year, 12, 31), 0]
		w = 0
		
		while date.year == year:
			if date.weekday() == 0:
				weeks[w][0] = date
	
			if date.weekday() <= 4 and h[date.month-1][date.day-1] == 0:
				weeks[w][2] += 8
	
			if date.weekday() == 6:
				weeks[w][1] = date
				w += 1
			
			date += one_day
	
		if date.weekday() == 0:
			w -= 1
		else:
			weeks[w][1] = (date - one_day)
			
		return weeks[0:w+1]


	@decorator.oauth_required
	def getHolidays(self, nickname, year):
		h = range(12)
		for i in range(12):
			h[i] = range(31)
			for j in range(31):
				h[i][j] = 0

#		http = decorator.http()
#		timeMin = str(year) + '-01-01T00:00:00Z'
#		timeMax = str(year + 1) + '-01-01T00:00:00Z'
#		request = service.events().list(calendarId = settings.CALENDAR_ID, timeMin = timeMin, timeMax = timeMax)
#		events = request.execute(http=http)

		events = {'items': [
				{'start': {'date': '2015-01-02'}},
				{'start': {'date': '2015-01-05'}},
				{'start': {'date': '2015-01-07'}},
				{'start': {'date': '2015-01-12'}},
				{'start': {'date': '2015-01-15'}},
				{'start': {'date': '2015-01-21'}}
			]}
		
		while 1:
			items = events['items']
			for i in range(len(items)):
				startdate = items[i]['start']['date']
				m = int(startdate[5:7])
				d = int(startdate[8:10])
				h[m-1][d-1] = 1
				
			if 'nextPageToken' in events:
				pageToken = events['nextPageToken']
				request = service.events().list(calendarId = settings.CALENDAR_ID, timeMin = timeMin, timeMax = timeMax, pageToken = pageToken)
				events = request.execute(http=http)
				continue
			break
		
		return h

	
	def showDashboard(self, nickname, year):
		weeks = self.getWeeks(nickname, year)
		logout_url = users.create_logout_url('/')
		
		template_values = {
			'logout_url': logout_url,
			'weeks': weeks
		}
		
		template = JINJA_ENVIRONMENT.get_template('dashboard.html')
		self.response.write(template.render(template_values))


application = webapp2.WSGIApplication([
	('/dashboard', Dashboard),
	(decorator.callback_path, decorator.callback_handler()),
], debug=True)
