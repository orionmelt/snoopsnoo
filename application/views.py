"""
views.py

URL route handlers

"""
from google.appengine.api import memcache
from google.appengine.ext import ndb

from flask import request, render_template, flash, url_for, redirect, session, g, abort, Markup, jsonify
from itsdangerous import URLSafeSerializer
from decorators import login_required, admin_required
from math import pow

#TODO - flask_cache

from application import app
from models import 	User, Feedback, ErrorLog, SubredditCategory, Subreddit, Category, CategoryTree, \
					PredefinedCategorySuggestion, ManualCategorySuggestion, SubredditRelation, PreprocessedItem

import sys, logging
import json, markdown, random

def uniq(seq):
    seen = set()
    seen_add = seen.add
    return [ x for x in seq if not (x in seen or seen_add(x))]

def get_all_subreddit_categories():
	all_subreddit_categories = memcache.get("all_subreddit_categories")
	
	if not all_subreddit_categories:
		p = PreprocessedItem.get_by_id("all_subreddit_categories")
		if p:
			all_subreddit_categories = json.loads(p.data)
			memcache.add("all_subreddit_categories", all_subreddit_categories)

	return all_subreddit_categories

def get_subreddits_root():
	root = memcache.get("subreddits_root")
	if not root:
		root = CategoryTree.get_by_id("reddit")
		memcache.add("subreddits_root", root)
	return root

def home():
    return render_template('index.html')

def about():
    return render_template('about.html')

def random_profile():
	r = ndb.Key("User", random.randrange(pow(2,52)-1))
	keys = User.query(User.key > r).fetch(1000,keys_only=True)
	if not keys:
		User.query(User.key < r).fetch(1000,keys_only=True)
	key = random.choice(keys)
	return redirect("/u/"+key.get().username)

def check_user(username):
	user = User.query(User.username_lower == username.lower()).get()
	if user:
		return "OK"
	else:
		user = User.query(User.username == username).get()
		if user:
			return "OK"
		else:
			return "NOT_FOUND"

def user_profile(username):
	user = User.query(User.username_lower == username.lower()).get()
	if not user:
		user = User.query(User.username == username).get()
	if not user:
		return render_template('blank_profile.html', username=username)

	if "version" in user.data and user.data["version"] in [2,3]:
		user.data["summary"]["comments"]["best"]["text"] = 	Markup(markdown.markdown(user.data["summary"]["comments"]["best"]["text"])) \
															  	if user.data["summary"]["comments"]["best"]["text"] else None
		user.data["summary"]["comments"]["worst"]["text"] = 	Markup(markdown.markdown(user.data["summary"]["comments"]["worst"]["text"])) \
																	if user.data["summary"]["comments"]["worst"]["text"] else None
	else:
		user.data["stats"]["basic"]["comments"]["best"]["text"] = 	Markup(markdown.markdown(user.data["stats"]["basic"]["comments"]["best"]["text"])) \
																  	if user.data["stats"]["basic"]["comments"]["best"]["text"] else None
		user.data["stats"]["basic"]["comments"]["worst"]["text"] = 	Markup(markdown.markdown(user.data["stats"]["basic"]["comments"]["worst"]["text"])) \
																	if user.data["stats"]["basic"]["comments"]["worst"]["text"] else None
	return render_template('user_profile.html', user=user, data=json.dumps(user.data))

def update_user():
	data=request.get_json()
	if not data:
		return "NO_DATA"
	username = data["username"]
	user = User.query(User.username_lower == username.lower()).get()
	data_version = data["version"]
	if user:
		user.username = username
		user.data_version = data_version
		user.data = data
		user.put()
	else:
		user = User(
					username=username,
					data_version=data_version,
					data=data
				)
		user.put()
	return "OK"

def process_feedback():
	username = request.args.get("u")
	data_key = request.args.get("k")
	data_value = request.args.get("v")
	feedback = request.args.get("f")=="1"
	f = Feedback(
			username=username,
			data_key=data_key,
			data_value=data_value,
			feedback=feedback
		)
	f.put()
	return "OK"

def error_log():
	username = request.args.get("u")
	error_type = request.args.get("t")
	error_message = request.args.get("m")
	e = ErrorLog(
			username=username,
			error_type=error_type,
			error_message=error_message
		)
	e.put()
	return "OK"

def insert_subreddit_category():
	page_id = int(request.form.get("page_id"))
	page_user = request.form.get("page_user")
	subreddit = request.form.get("subreddit")
	level_name = request.form.get("level_name")
	level_value = request.form.get("level_value")
	c = SubredditCategory(
			page_id=page_id,
			page_user=page_user,
			subreddit=subreddit,
			level_name=level_name,
			level_value=level_value
		)
	c.put()
	return ""

def subreddits_home():

	root = get_subreddits_root()
	intro_items = [
		{"id":"reddit_music_metal", "caption": "Discuss metal music.", "icon": "music"},
		{"id":"reddit_hobbies-and-interests_languages", "caption": "Learn a new language.", "icon": "language"},
		{"id":"reddit_sports_soccer", "caption": "Connect with soccer fans.", "icon": "soccer"},
		{"id":"reddit_business_jobs-and-careers", "caption": "Get help with finding a job.", "icon": "jobs"},
		{"id":"reddit_entertainment_television", "caption": "Talk about your favorite TV shows.", "icon": "tv"},
		{"id":"reddit_lifestyle_food-and-beverages_cooking", "caption": "Learn how to cook.", "icon": "cooking"},
		{"id":"reddit_technology_programming", "caption": "Learn programming.", "icon": "code"},
		{"id":"reddit_hobbies-and-interests_outdoors_cycling", "caption": "Share your love for cycling.", "icon": "cycling"},
	]
	return render_template(
		'subreddits_home.html', 
		root=json.loads(root.data), 
		subreddit_count=root.subreddit_count, 
		last_updated=root.last_updated, 
		intro_items=random.sample(intro_items,3)
	)

def subreddits_category(level1,level2=None,level3=None):
	category_id = "reddit_"+level1.lower()
	breadcrumbs_ids = [category_id]
	if level2:
		category_id += "_"+level2.lower()
		breadcrumbs_ids.append(category_id)
	if level3:
		category_id += "_"+level3.lower()
		breadcrumbs_ids.append(category_id)
	
	category = Category.get_by_id(category_id)

	if not category:
		abort(404)

	all_subreddit_categories = get_all_subreddit_categories()

	category_tree = [x for x in json.loads(CategoryTree.get_by_id(category_id).data)["children"] if "children" in x]
	breadcrumbs = [Category.get_by_id(x) for x in breadcrumbs_ids]

	cursor = request.args.get("c")
	is_prev = True if request.args.get("p") else False

	subreddits, prev_bookmark, next_bookmark = \
		return_query_page(query_class=Subreddit, bookmark=cursor, is_prev=is_prev, equality_filters={'parent_id':category_id}, orders={'subscribers':'-'})

	return render_template(
		'subreddits_category.html',
		subreddits=subreddits, 
		category=category, 
		cat_tree=category_tree, 
		breadcrumbs=breadcrumbs, 
		prev=prev_bookmark, 
		next=next_bookmark,
		all_subreddit_categories=all_subreddit_categories
	)

def subreddit(subreddit_name):
	subreddit_name=subreddit_name.lower()
	s = Subreddit.query(Subreddit.display_name_lower==subreddit_name).get()
	if not s:
		return render_template("subreddit_not_found.html", subreddit=subreddit_name)

	breadcrumbs = []
	for i,c in enumerate(s.parent_id.split("_")):
		breadcrumbs.append(Category.get_by_id("_".join(s.parent_id.split("_")[:i+1])))

	related_target_ids = \
		[ndb.Key("Subreddit", r.target) for r in SubredditRelation.query(SubredditRelation.source==s.key.id()).order(-SubredditRelation.weight).fetch(5)]
	related_source_ids = \
		[ndb.Key("Subreddit", r.source) for r in SubredditRelation.query(SubredditRelation.target==s.key.id()).order(-SubredditRelation.weight).fetch(5)]
	related_subreddits = [x for x in ndb.get_multi(uniq(related_source_ids+related_target_ids)) if x]
	
	all_subreddit_categories = get_all_subreddit_categories()
	
	return render_template(
		'subreddit.html', 
		subreddit=s, 
		breadcrumbs=breadcrumbs[1:], 
		all_subreddit_categories=all_subreddit_categories, 
		related_subreddits=related_subreddits
	)

def subreddit_frontpage():
	data=request.get_json()
	return render_template('subreddit_frontpage.html', front_page=data)

def suggest_subreddit_category():
	subreddit_id = request.form.get("subreddit_id")
	category_id = request.form.get("category_id")
	suggested_category = request.form.get("suggested_category")
	if not suggested_category:
		c = PredefinedCategorySuggestion(
			subreddit_id=subreddit_id,
			category_id=category_id
		)
		c.put()
	else:
		c = ManualCategorySuggestion(
			subreddit_id=subreddit_id,
			category_id=category_id,
			suggested_category=suggested_category
		)
		c.put()
	return "OK"

def find_subreddit():
	input_subreddit = request.form.get("subreddit").lower()
	subreddit = Subreddit.query(Subreddit.display_name_lower == input_subreddit).get()
	if subreddit:
		return redirect("/r/"+subreddit.display_name)
	else:
		return render_template("subreddit_not_found.html", subreddit=input_subreddit)


def subreddits_graph():
	return render_template('subreddits_graph.html')

def subreddits_graph_json():
	root = CategoryTree.get_by_id("reddit")
	return jsonify(json.loads(root.data))


@admin_required
def delete_user(username):
	user = User.query(User.username == username).get()
	user.key.delete()
	return "OK"

def warmup():
    """App Engine warmup handler
    See http://code.google.com/appengine/docs/python/config/appconfig.html#Warming_Requests

    """
    return ''

# From https://github.com/janscas/ndb-gae-pagination
def return_query_page(query_class, size=25, bookmark=None, is_prev=None, equality_filters=None, orders=None):
    """
    Generate a paginated result on any class
    Param query_class: The ndb model class to query
    Param size: The size of the results
    Param bookmark: The urlsafe cursor of the previous queris. First time will be None
    Param is_prev: If your requesting for a next result or the previous ones
    Param equality_filters: a dictionary of {'property': value} to apply equality filters only
    Param orders: a dictionary of {'property': '-' or ''} to order the results like .order(cls.property)
    Return: a tuple (list of results, Previous cursor bookmark, Next cursor bookmark)
    """
    if bookmark:
        cursor = ndb.Cursor(urlsafe=bookmark)
    else:
        is_prev = None
        cursor = None

    q = query_class.query()
    try:
        for prop, value in equality_filters.iteritems():
            q = q.filter(getattr(query_class, prop) == value)

        q_forward = q.filter()
        q_reverse = q.filter()

        for prop, value in orders.iteritems():
            if value == '-':
                q_forward = q_forward.order(-getattr(query_class, prop))
                q_reverse = q_reverse.order(getattr(query_class, prop))
            else:
                q_forward = q_forward.order(getattr(query_class, prop))
                q_reverse = q_reverse.order(-getattr(query_class, prop))
    except:
        return None, None, None
    if is_prev:
        qry = q_reverse
        new_cursor = cursor.reversed() if cursor else None
    else:
        qry = q_forward
        new_cursor = cursor if cursor else None

    results, new_cursor, more = qry.fetch_page(size, start_cursor=new_cursor)
    if more and new_cursor:
        more = True
    else:
        more = False

    if is_prev:
        prev_bookmark = new_cursor.reversed().urlsafe() if more else None
        next_bookmark = bookmark
        results.reverse()
    else:
        prev_bookmark = bookmark
        next_bookmark = new_cursor.urlsafe() if more else None

    return results, prev_bookmark, next_bookmark
