"""
Initialize Flask app

"""
from flask import Flask
import os
from flask_debugtoolbar import DebugToolbarExtension
from werkzeug.debug import DebuggedApplication

app = Flask('application')

# GAE doesn't seem to support OS environment variables, so we look at
# SERVER_SOFTWARE to set dev/prod app config.
if 'Development' in os.getenv('SERVER_SOFTWARE'):
    os.environ['FLASK_CONF'] = 'DEV'

if os.getenv('FLASK_CONF') == 'DEV_PROFILER':
	#development settings n
    app.config.from_object('application.settings.Development')
	# Flask-DebugToolbar (only enabled when DEBUG=True)
    toolbar = DebugToolbarExtension(app)
    
    # Google app engine mini profiler
    # https://github.com/kamens/gae_mini_profiler
    app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)

    from gae_mini_profiler import profiler, templatetags 
    @app.context_processor
    def inject_profiler():
        return dict(profiler_includes=templatetags.profiler_includes())
    app.wsgi_app = profiler.ProfilerWSGIMiddleware(app.wsgi_app)

elif os.getenv('FLASK_CONF') == 'TEST':
    app.config.from_object('application.settings.Testing')

else:
    app.config.from_object('application.settings.Production')

from jinja_filters import format_date, time_since, format_month, format_day, safe_markdown, from_timestamp

# Enable jinja2 loop controls extension
app.jinja_env.add_extension('jinja2.ext.loopcontrols')
app.jinja_env.add_extension('jinja2.ext.autoescape')

app.jinja_env.filters['format_date'] = format_date
app.jinja_env.filters['format_month'] = format_month
app.jinja_env.filters['format_day'] = format_day
app.jinja_env.filters['time_since'] = time_since
app.jinja_env.filters['markdown'] = safe_markdown
app.jinja_env.filters['from_timestamp'] = from_timestamp

# Pull in URL dispatch routes
import urls