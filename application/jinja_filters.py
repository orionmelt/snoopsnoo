"""

Custom jinja2 filters

"""

from datetime import datetime
import re
import os

import jinja2
import markdown

#Change %e to %d if running on Windows
def format_date(value, format_string='%b %d, %Y'):
  """Returns formatted date given a datetime object."""
  return value.strftime(format_string)

def format_month(value, format_string='%b'):
  """Returns month given a datetime object."""
  return value.strftime(format_string)

def format_day(value, format_string='%e'):
  """Returns day given a datetime object."""
  return value.strftime(format_string)

def from_timestamp(value):
  """Returns datetime object given a timestamp."""
  return datetime.fromtimestamp(int(value))

def time_since(value):
  """Returns textual representation of time since given datetime object."""
  now = datetime.utcnow()
  diff = now - value
  periods = (
    (diff.days / 365, "year", "years"),
    (diff.days / 30, "month", "months"),
    (diff.days / 7, "week", "weeks"),
    (diff.days, "day", "days"),
    (diff.seconds / 3600, "hour", "hours"),
    (diff.seconds / 60, "minute", "minutes"),
    (diff.seconds, "second", "seconds"),
  )
  for period, singular, plural in periods:
    if period:
      return "%d %s" % (period, singular if period == 1 else plural)
  return "a few seconds"

def safe_markdown(text):
  """Returns marked up text given markdown text."""
  return jinja2.Markup(markdown.markdown(text))

def strip_links(text):
  """Removes markdown links from given text."""
  return re.sub(
    r"\[(.*?)\]\s*\(.+?\)", r"\1",
    text,
    re.IGNORECASE|re.MULTILINE
  )

def current_version(text):
  """Returns current app version"""
  return os.environ['CURRENT_VERSION_ID']
