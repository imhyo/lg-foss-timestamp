from google.appengine.ext import ndb

class Timestamp(ndb.Model):
	start = ndb.DateTimeProperty(auto_now_add=True)
	finish = ndb.DateTimeProperty(auto_now_add=False)
	user = ndb.UserProperty(indexed=False)
	content = ndb.StringProperty(indexed=False)


class User(ndb.Model):
	nickname = ndb.StringProperty()
