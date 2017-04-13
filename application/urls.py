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
app.add_url_rule("/random", "random_user", view_func=views.random_user)
app.add_url_rule("/random-user", "random_user", view_func=views.random_user)

# User page
app.add_url_rule("/u/<username>", "user_profile", view_func=views.user_profile)

# User existence check page
app.add_url_rule("/check/<username>", "check_user", view_func=views.check_user)

# Update user data page
app.add_url_rule(
  "/update",
  "update_user",
  view_func=views.update_user,
  methods=["POST"]
)

# Feedback page
app.add_url_rule(
  "/feedback",
  "save_synopsis_feedback",
  view_func=views.save_synopsis_feedback
)

# Subreddit Recommendation Feedback page
app.add_url_rule(
  "/sub-reco-feedback",
  "save_sub_reco_feedback",
  view_func=views.save_sub_reco_feedback
)

# Error log page
app.add_url_rule("/error-log", "save_error", view_func=views.save_error)

# Delete page
app.add_url_rule("/delete/<username>", "delete", view_func=views.delete_user)

# Subreddits Home page
app.add_url_rule(
  "/subreddits/", "subreddits_home", view_func=views.subreddits_home
)

# Subreddit Recommendations
app.add_url_rule(
  "/subreddits/recommend/<subreddits>",
  "get_recommended_subreddits",
  view_func=views.get_recommended_subreddits
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

# Subreddit metrics API
app.add_url_rule(
  "/api/r/<subreddit_id>/metrics",
  "subreddit_metrics",
  view_func=views.subreddit_metrics
)

# Subreddit category API
app.add_url_rule(
  "/api/r/<subreddit_name>/category",
  "subreddit_category",
  view_func=views.subreddit_category
)

# User data API
app.add_url_rule(
  "/api/u/<username>",
  "user_data",
  view_func=views.get_user_data
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
  "save_sub_category_suggestion",
  view_func=views.save_sub_category_suggestion,
  methods=["POST"]
)

# Stage Subreddit Category page
app.add_url_rule(
  "/stage-subreddit-category",
  "stage_sub_category",
  view_func=views.stage_sub_category,
  methods=["POST"]
)

# Subreddit Search Results page
app.add_url_rule(
  "/subreddits/search",
  "search_subreddits",
  view_func=views.search_subreddits,
  methods=["GET"]
)

# Add new subreddits
app.add_url_rule(
  "/subreddits/add-new",
  "add_new_subs",
  view_func=views.add_new_subs,
  methods=["GET"]
)

# Callback for counting subreddits by category
app.add_url_rule(
  "/subreddits/count-subreddits-callback",
  "count_subreddits_callback",
  view_func=views.count_subreddits_callback,
  methods=["POST"]
)

# Export subredits MapReduce handler
app.add_url_rule(
  "/jobs/export-subreddits-to-bigquery",
  "export_subreddits_handler",
  view_func=views.export_subreddits_handler
)

# Export synopsis feedback MapReduce handler
app.add_url_rule(
  "/jobs/export-feedback-to-bigquery",
  "export_synopsis_feedback_handler",
  view_func=views.export_synopsis_feedback_handler
)

# Export predefined category suggestion MapReduce handler
app.add_url_rule(
  "/jobs/export-predef-suggestions-to-bigquery",
  "export_predefined_category_suggestion_handler",
  view_func=views.export_predefined_category_suggestion_handler
)

# Export manual category suggestion MapReduce handler
app.add_url_rule(
  "/jobs/export-manual-suggestions-to-bigquery",
  "export_manual_category_suggestion_handler",
  view_func=views.export_manual_category_suggestion_handler
)

# Export user summary MapReduce handler
app.add_url_rule(
  "/jobs/export-user-summary-to-bigquery",
  "export_user_summary_handler",
  view_func=views.export_user_summary_handler
)

app.add_url_rule(
  "/jobs/update-subscribers",
  "update_subscribers_handler",
  view_func=views.update_subscribers_handler
)

app.add_url_rule(
  "/jobs/update-trends",
  "update_trends",
  view_func=views.update_trends
)

app.add_url_rule(
  "/jobs/update-search-subscribers",
  "update_search_subscribers",
  view_func=views.update_search_subscribers
)

app.add_url_rule(
  "/jobs/process-category-stage",
  "process_sub_category_stage",
  view_func=views.process_sub_category_stage
)

app.add_url_rule(
  "/jobs/update-preprocessed-subreddit-categories",
  "update_preprocessed_subreddit_categories",
  view_func=views.update_preprocessed_subreddit_categories
)

app.add_url_rule(
  "/sitemap.xml",
  "sitemap",
  view_func=views.sitemap
)

app.add_url_rule(
  "/nibble/reddit-history/",
  "reddit_history",
  view_func=views.reddit_history
)

app.add_url_rule(
  "/nibble/reddit-first-post/",
  "first_post",
  view_func=views.first_post
)

app.add_url_rule(
  "/nibble/get-first-post",
  "get_first_post",
  view_func=views.get_first_post,
  methods=["POST"]
)

## Error handlers
@app.errorhandler(404)
def page_not_found(exception):
  """Return 404 page."""
  return render_template("404.html", exception=exception), 404

# Handle 500 errors
@app.errorhandler(500)
def server_error(exception):
  """Return 500 page."""
  return render_template("500.html", exception=exception), 500
