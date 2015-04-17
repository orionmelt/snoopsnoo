import os

from flask import Flask

from jinja_filters import (
    format_date, time_since, format_month, format_day, 
    safe_markdown, from_timestamp, strip_links
)

app = Flask(__name__)

if os.getenv('FLASK_CONF') == 'TEST':
    app.config.from_object('application.settings.Testing')
elif 'SERVER_SOFTWARE' in os.environ and os.environ['SERVER_SOFTWARE'].startswith('Dev'):
    app.config.from_object('application.settings.Development')
else:
    app.config.from_object('application.settings.Production')

app.jinja_env.add_extension("jinja2.ext.loopcontrols")
app.jinja_env.add_extension("jinja2.ext.autoescape")

app.jinja_env.filters["format_date"] = format_date
app.jinja_env.filters["format_month"] = format_month
app.jinja_env.filters["format_day"] = format_day
app.jinja_env.filters["time_since"] = time_since
app.jinja_env.filters["markdown"] = safe_markdown
app.jinja_env.filters["from_timestamp"] = from_timestamp
app.jinja_env.filters["strip_links"] = strip_links

# Pull in URL dispatch routes
import urls