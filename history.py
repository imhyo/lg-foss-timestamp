import datetime
import logging
import pytz

from google.appengine.api import users
from google.appengine.ext import ndb

import data_model
import user_auth


# Returns the list of working history.
def getHistory(user = None, min = None, max = None, num = 0):
	if user is None:
		user = users.get_current_user()

	utc = pytz.timezone('UTC')
	kst = pytz.timezone('Asia/Seoul')
		
	query = data_model.Timestamp.query(
		ancestor = user_auth.get_user_key(user)).order(-data_model.Timestamp.start)
	if min:
		min_time = datetime.datetime(min.year, min.month, min.day, 0, 0, 0)
		min_time = kst.localize(min_time).astimezone(utc)
		query = query.filter(data_model.Timestamp.start >= min_time)
	if max:
		max1 = max + datetime.timedelta(1)
		max_time = datetime.datetime(max1.year, max1.month, max1.day, 0, 0, 0)
		max_time = kst.localize(max_time).astimezone(utc)
		query = query.filter(data_model.Timestamp.start < max_time)
	
	if num > 0:
		return (query.fetch(num))
	else:
		return (query.fetch())
