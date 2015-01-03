"""
urls.py

URL dispatch route mappings and error handlers

"""
from flask import render_template

from application import app
from application import views


## URL dispatch rules
# App Engine warm up handler
# See http://code.google.com/appengine/docs/python/config/appconfig.html#Warming_Requests
app.add_url_rule('/_ah/warmup', 'warmup', view_func=views.warmup)

# Home page
app.add_url_rule('/', 'home', view_func=views.home)

# Random user page
app.add_url_rule('/random', 'random', view_func=views.random_profile)

# Source page
#app.add_url_rule('/source', 'source', view_func=views.source)

# User page
app.add_url_rule('/u/<username>', 'user_profile', view_func=views.user_profile)

# User existence check page
app.add_url_rule('/cu/<username>', 'check_user', view_func=views.check_user)

# Update user data page
app.add_url_rule('/update_user', 'update_user', view_func=views.update_user, methods=["POST"])

# Feedback page
app.add_url_rule('/feedback', 'feedback', view_func=views.process_feedback)

# Error log page
app.add_url_rule('/error-log', 'error_log', view_func=views.error_log)

# Delete page
app.add_url_rule('/del/<username>', 'delete', view_func=views.delete_user)

# User profile page
#app.add_url_rule('/u/<username>', 'user_profile', view_func=views.user_profile)

## Error handlers
# Handle 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Handle 500 errors
@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

