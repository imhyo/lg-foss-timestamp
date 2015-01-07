import os
import datetime
import pytz
import jinja2
import webapp2
import logging

from google.appengine.api import users
from google.appengine.ext import ndb
from apiclient.discovery import build
from google.appengine.ext import webapp
from oauth2client.appengine import OAuth2Decorator

import settings
import user_auth
import data_model
import history


JINJA_ENVIRONMENT = jinja2.Environment(
	loader = jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'views')),
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
		self.showDashboard()
		
	def post(self):
		self.showDashboard()

	def getWeekOfYear(self, year, date):
		new_year = datetime.date(year, 1, 1)
		monday = new_year - datetime.timedelta(1) * new_year.weekday()
		t = date - monday
		return (t.days/7)
		
	def getEmptyWeeks(self, year, h):
		weeks = range(54)
		one_day = datetime.timedelta(1)
		today = datetime.date.today()
		date = datetime.date(year, 1, 1)
		end_date = datetime.date(year, 12, 31)
		
		for i in range(54):
			weeks[i] = [datetime.date(year, 1, 1), datetime.date(year, 12, 31), 0.0, 0]
		w = 0
		
		while date.year == year and date <= today:
			if date.weekday() == 0:
				weeks[w][0] = date
	
			if date.weekday() <= 4 and h[date.month-1][date.day-1] == 0:
				weeks[w][3] += 8
	
			if date.weekday() == 6:
				weeks[w][1] = date
				w += 1
				
			date += one_day
	
		if date.weekday() == 0:
			w -= 1
		else:
			date -= one_day
			weeks[w][1] = date
			
		return weeks[0:w+1]

		
	def calcWorkingHours(self, nickname, year, weeks):
		utc = pytz.timezone('UTC')
		kst = pytz.timezone('Asia/Seoul')
		user = users.get_current_user()
		sd = datetime.date(year, 1, 1)
		ed = datetime.date(year, 12, 31)
		timestamps = history.getHistory(min = sd, max = ed)
		
		for timestamp in timestamps:
			if (timestamp.finish is None):
				continue
			sdt = utc.localize(timestamp.start).astimezone(kst)
			fdt = utc.localize(timestamp.finish).astimezone(kst)
			timedelta = fdt - sdt

			sd = sdt.date()
			w = self.getWeekOfYear(year, sd)
			weeks[w][2] += timedelta.total_seconds() / 3600.0
		
	def roundWorkingHours(self, weeks):
		for week in weeks:
			week[2] = round(week[2], 1)
		
	def getWeeks(self, nickname, year):
		h = self.getHolidays(nickname, year)
		weeks = self.getEmptyWeeks(year, h)
		self.calcWorkingHours(nickname, year, weeks)
		self.roundWorkingHours(weeks)
		return weeks


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

	
	def showDashboard(self):
		user = users.get_current_user()
		year_str = self.request.get('year')
		if (not year_str):
			year = datetime.date.today().year
		else:
			year = int(year_str)
		weeks = self.getWeeks(user.nickname(), year)
		
		template_values = {
			'weeks': weeks,
		}
		
		template = JINJA_ENVIRONMENT.get_template('dashboard.html')
		self.response.write(template.render(template_values))


application = webapp2.WSGIApplication([
	('/dashboard', Dashboard),
	(decorator.callback_path, decorator.callback_handler()),
], debug=True)
