"""
models.py

App Engine datastore models

"""

from google.appengine.ext import ndb
import re

class User(ndb.Model):
    """
    Models an individual user entry.

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
    """
    Models a feedback entry that records user feedback about synopsis items.
    """
    username = ndb.StringProperty()
    log_date = ndb.DateTimeProperty(auto_now_add=True)
    data_key = ndb.StringProperty()
    data_value = ndb.StringProperty(indexed=False)
    feedback = ndb.BooleanProperty()

class ErrorLog(ndb.Model):
    """
    Models an error log entry.
    """
    username = ndb.StringProperty()
    log_date = ndb.DateTimeProperty(auto_now_add=True)
    error_type = ndb.StringProperty()
    error_message = ndb.StringProperty(indexed=False)

class Category(ndb.Model):
    """
    Models a category entry. A category could be a top-level
    category (level 1), subcategory (level 2), or a third-level
    description (level 3).
    """
    display_name = ndb.StringProperty()
    pretty_url = ndb.ComputedProperty(
        lambda self: re.sub(
            r'([^\s\w]|_)+', '', self.display_name.lower()
        ).replace(" ", "-")
    )
    subreddit_count = ndb.IntegerProperty()
    last_updated = ndb.DateTimeProperty(auto_now=True)
    parent_id = ndb.StringProperty()

class Subreddit(ndb.Model):
    """
    Models a subreddit entry.
    """
    display_name = ndb.StringProperty()
    display_name_lower = ndb.ComputedProperty(
        lambda self: self.display_name.lower()
    )
    title = ndb.StringProperty()
    public_description = ndb.StringProperty(indexed=False)
    description_html = ndb.TextProperty()
    subreddit_type = ndb.IntegerProperty()
    submission_type = ndb.IntegerProperty()
    created_utc = ndb.DateTimeProperty()
    subscribers = ndb.IntegerProperty()
    over18 = ndb.BooleanProperty()
    last_updated = ndb.DateTimeProperty(auto_now=True)
    parent_id = ndb.StringProperty()

class CategoryTree(ndb.Model):
    """Models a category tree entry.
    """
    last_updated = ndb.DateTimeProperty(auto_now=True)
    subreddit_count = ndb.IntegerProperty()
    data = ndb.JsonProperty()

class PredefinedCategorySuggestion(ndb.Model):
    """
    Models a suggested category (predefined) for a subreddit.
    """
    log_date = ndb.DateTimeProperty(auto_now_add=True)
    subreddit_display_name = ndb.StringProperty()
    subreddit_display_name_lower = ndb.ComputedProperty(
        lambda self: self.subreddit_display_name.lower()
    )
    category_id = ndb.StringProperty()

class ManualCategorySuggestion(ndb.Model):
    """
    Models a suggested category (manual) for a subreddit.
    """
    log_date = ndb.DateTimeProperty(auto_now_add=True)
    subreddit_display_name = ndb.StringProperty()
    subreddit_display_name_lower = ndb.ComputedProperty(
        lambda self: self.subreddit_display_name.lower()
    )
    category_id = ndb.StringProperty()
    suggested_category = ndb.StringProperty(indexed=False)

class SubredditRelation(ndb.Model):
    """
    Models a related subreddit entry.
    """
    last_updated = ndb.DateTimeProperty(auto_now=True)
    source = ndb.StringProperty()
    target = ndb.StringProperty()
    weight = ndb.FloatProperty()

class PreprocessedItem(ndb.Model):
    """
    Models preprocessed item entry (for performance reasons).
    """
    last_updated = ndb.DateTimeProperty(auto_now=True)
    data = ndb.JsonProperty()

class SubredditRecommendationFeedback(ndb.Model):
    """
    Models a feedback entry that records user feedback about
    subreddit recommendations.
    """
    username = ndb.StringProperty(indexed=False)
    log_date = ndb.DateTimeProperty(auto_now_add=True)
    input_subreddits = ndb.StringProperty(indexed=False)
    recommended_subreddit = ndb.StringProperty()
    feedback = ndb.BooleanProperty()

class SearchQuery(ndb.Model):
    """
    Models a search query entry.
    """
    kind = ndb.IntegerProperty()
    log_date = ndb.DateTimeProperty(auto_now_add=True)
    query_text = ndb.StringProperty(indexed=False)
    country = ndb.StringProperty(indexed=False)
    region = ndb.StringProperty(indexed=False)
    city = ndb.StringProperty(indexed=False)
    latlong = ndb.StringProperty(indexed=False)
    remote_addr = ndb.StringProperty(indexed=False)


