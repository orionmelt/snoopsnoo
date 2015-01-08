"""
models.py

App Engine datastore models

"""

from google.appengine.ext import ndb

class User(ndb.Model):
	"""Models an individual user entry.

	Attributes:
		username        - reddit username
		analyze_date    - Last when analyzed
		data            - JSON data
	"""
	username = ndb.StringProperty()
	username_lower = ndb.ComputedProperty(lambda self: self.username.lower())
	version = ndb.IntegerProperty()
	last_updated = ndb.DateTimeProperty(auto_now=True)
	data = ndb.JsonProperty()

class Feedback(ndb.Model):
	"""Models a feedback entry.
	"""
	username = ndb.StringProperty()
	log_date = ndb.DateTimeProperty(auto_now_add=True)
	data_key = ndb.StringProperty(indexed=False)
	data_value = ndb.StringProperty(indexed=False)
	feedback = ndb.BooleanProperty()

class ErrorLog(ndb.Model):
	"""Models an error log entry.
	"""
	username = ndb.StringProperty()
	log_date = ndb.DateTimeProperty(auto_now_add=True)
	error_type = ndb.StringProperty()
	error_message = ndb.StringProperty(indexed=False)
