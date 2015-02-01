"""
views.py

URL route handlers

"""
from google.appengine.api import memcache
from google.appengine.ext import ndb

from flask import request, render_template, flash, url_for, redirect, session, g, abort, Markup
from itsdangerous import URLSafeSerializer
from decorators import login_required, admin_required
from math import pow

#TODO - flask_cache

from application import app
from models import User, Feedback, ErrorLog, SubredditCategory, Subreddit, Category, CategoryTree

import sys, logging
import json, markdown, random

def home():
    return render_template('index.html')

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

def subreddits_directory_home():
	root = CategoryTree.get_by_id("reddit")
	return render_template('directory_home.html', root=json.loads(root.data), subreddit_count=root.subreddit_count, last_updated=root.last_updated)

def subreddits_directory_category(level1,level2=None,level3=None):
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

	category_tree = [x for x in json.loads(CategoryTree.get_by_id(category_id).data)["children"] if "children" in x]
	breadcrumbs = [Category.get_by_id(x) for x in breadcrumbs_ids]

	cursor = request.args.get("c")
	is_prev = True if request.args.get("p") else False

	subreddits, prev_bookmark, next_bookmark = \
		return_query_page(query_class=Subreddit, bookmark=cursor, is_prev=is_prev, equality_filters={'parent_id':category_id}, orders={'subscribers':'-'})

	return render_template(
		'directory_category.html',
		subreddits=subreddits, 
		category=category, 
		cat_tree=cat_tree, 
		breadcrumbs=breadcrumbs, 
		prev=prev_bookmark, 
		next=next_bookmark
	)

def subreddit(subreddit_name):
	subreddit_name=subreddit_name.lower()
	s = Subreddit.query(Subreddit.display_name_lower==subreddit_name).get()
	breadcrumbs = []
	for i,c in enumerate(s.parent_id.split("_")):
		breadcrumbs.append(Category.get_by_id("_".join(s.parent_id.split("_")[:i+1])))
	if not s:
		abort(404)
	return render_template('subreddit.html', subreddit=s, breadcrumbs=breadcrumbs[1:])

def front_page():
	data=request.get_json()
	return render_template('front_page.html', front_page=data)

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
