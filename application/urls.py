"""
urls.py

URL dispatch route mappings and error handlers

"""
from flask import render_template

from application import app
from application import views


## URL dispatch rules
# App Engine warm up handler
# See https://cloud.google.com/appengine/docs/python/config/appconfig
app.add_url_rule("/_ah/warmup", "warmup", view_func=views.warmup)

# Home page
app.add_url_rule("/", "home", view_func=views.home)

# About page
app.add_url_rule("/about/", "about", view_func=views.about)

# Random user page
app.add_url_rule("/random", "random_profile", view_func=views.random_profile)

app.add_url_rule(
    "/random-user", "random_profile", view_func=views.random_profile
)

# User page
app.add_url_rule("/u/<username>", "user_profile", view_func=views.user_profile)

# User existence check page
app.add_url_rule("/check/<username>", "check_user", view_func=views.check_user)

# Update user data page
app.add_url_rule(
    "/update", "update_user", view_func=views.update_user, methods=["POST"]
)

# Feedback page
app.add_url_rule("/feedback", "feedback", view_func=views.process_feedback)

# Subreddit Recommendation Feedback page
app.add_url_rule(
    "/sub-reco-feedback", 
    "subreddit_recommendation_feedback", 
    view_func=views.process_subreddit_recommendation_feedback
)

# Error log page
app.add_url_rule("/error-log", "error_log", view_func=views.error_log)

# Delete page
app.add_url_rule("/delete/<username>", "delete", view_func=views.delete_user)

# Subreddits Home page
app.add_url_rule(
    "/subreddits/", "subreddits_home", view_func=views.subreddits_home
)

# Subreddit Recommendations
app.add_url_rule(
    "/subreddits/recommended/<subreddits>", 
    "recommended_subreddits", 
    view_func=views.recommended_subreddits
)

# Subreddits Category page
app.add_url_rule(
    "/subreddits/<level1>/", 
    "subreddits_category", 
    view_func=views.subreddits_category
)

app.add_url_rule(
    "/subreddits/<level1>/<level2>/", 
    "subreddits_category", 
    view_func=views.subreddits_category
)

app.add_url_rule(
    "/subreddits/<level1>/<level2>/<level3>/", 
    "subreddits_category", 
    view_func=views.subreddits_category
)

# Subreddit page
app.add_url_rule(
    "/r/<subreddit_name>", 
    "subreddit", 
    view_func=views.subreddit
)

# Subreddit Frontpage preview
app.add_url_rule(
    "/subreddit_frontpage", 
    "subreddit_frontpage", 
    view_func=views.subreddit_frontpage, 
    methods=["POST"]
)

# Subreddit Category Suggestion page
app.add_url_rule(
    "/suggest-subreddit-category", 
    "suggest_subreddit_category", 
    view_func=views.suggest_subreddit_category, 
    methods=["POST"]
)

# Find Subreddit page
app.add_url_rule(
    "/find-subreddit", 
    "find_subreddit", 
    view_func=views.find_subreddit, 
    methods=["POST"]
)

## Error handlers
# Handle 404 errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# Handle 500 errors
@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500
