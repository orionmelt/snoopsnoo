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
	data_version = ndb.IntegerProperty()
	date_added = ndb.DateTimeProperty(auto_now_add=True)
	last_updated = ndb.DateTimeProperty(auto_now=True)
	data = ndb.JsonProperty()

class Feedback(ndb.Model):
	"""Models a feedback entry that records user feedback about synopsis items.
	"""
	username = ndb.StringProperty()
	log_date = ndb.DateTimeProperty(auto_now_add=True)
	data_key = ndb.StringProperty()
	data_value = ndb.StringProperty(indexed=False)
	feedback = ndb.BooleanProperty()

class ErrorLog(ndb.Model):
	"""Models an error log entry.
	"""
	username = ndb.StringProperty()
	log_date = ndb.DateTimeProperty(auto_now_add=True)
	error_type = ndb.StringProperty()
	error_message = ndb.StringProperty(indexed=False)

class SubredditCategory(ndb.Model):
	"""Models a subreddit category entry that user entered in the Help Categorize Subreddits section.
	"""
	page_id = ndb.IntegerProperty()
	page_user = ndb.StringProperty()
	subreddit = ndb.StringProperty()
	level_name = ndb.StringProperty()
	level_value = ndb.StringProperty()

