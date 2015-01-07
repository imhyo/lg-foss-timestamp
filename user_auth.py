from google.appengine.api import users
from google.appengine.ext import ndb

import user_auth
import data_model


# Decorator function that checks if the user is a registered user for this system.
# '@auth_required' should be added in front of the function which requires the user to be already logged in.
def auth_required(handler):
	def check_login(self, *args, **kwargs):
		nickname = users.get_current_user().nickname()
		user_key = get_user_key(users.get_current_user())
		users_query = data_model.User(key = user_key).query()
		users_list = users_query.fetch(1)
		# if there is no entity corresponding to the user, redirect to the page saying the user has no authority to access the page.
		if (not users_list) or (users_list[0].nickname != nickname):
			self.redirect("/no_authority")
		else:
			return handler(self, *args, **kwargs)

	return check_login


# Returns the key corresponding to the user
def get_user_key(user):
	return ndb.Key('User', user.nickname())


