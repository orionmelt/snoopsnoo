from datetime import datetime
import re

import jinja2
import markdown

from application import app

#Change %e to %d if running on Windows
def format_date(value, format='%b %d, %Y'):
    return value.strftime(format)

def format_month(value, format='%b'):
    return value.strftime(format)

def format_day(value, format='%e'):
    return value.strftime(format)
    
def from_timestamp(value):
    return datetime.fromtimestamp(int(value))

def time_since(value):
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
    return jinja2.Markup(markdown.markdown(text))

def strip_links(text):
    return re.sub(
        r"\[(.*?)\]\s*\(.+?\)", r"\1", 
        text, 
        re.IGNORECASE|re.MULTILINE
    )
