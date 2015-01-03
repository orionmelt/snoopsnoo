"""
views.py

URL route handlers

"""
from google.appengine.api import memcache
from google.appengine.ext import ndb

from flask import request, render_template, flash, url_for, redirect, session, g, abort, Markup
from itsdangerous import URLSafeSerializer
from decorators import login_required, admin_required

#TODO - flask_cache

from application import app
from models import User, Feedback, ErrorLog

import sys, logging
from datetime import datetime, date
from uuid import uuid4
import json, urllib, markdown, random

def home():
    return render_template('index.html')

def random_profile():
	keys = User.query().fetch(keys_only=True)
	key = random.sample(keys, 1)[0]
	return redirect("/u/"+key.get().username)

def check_user(username):
	#user = User.get_by_id(username)
	user = User.query(User.username_lower == username.lower()).get()
	if user:
		return "OK"
	else:
		user = User.query(User.username == username).get()
		if user:
			return "OK"
		else:
			return "NO"

def user_profile(username):
	#user = User.get_by_id(username)
	user = User.query(User.username_lower == username.lower()).get()
	if not user:
		user = User.query(User.username == username).get()
	if not user:
		abort(404)
	user.data["stats"]["basic"]["comments"]["best"]["text"] = 	Markup(markdown.markdown(user.data["stats"]["basic"]["comments"]["best"]["text"])) \
															  	if user.data["stats"]["basic"]["comments"]["best"]["text"] else None
	user.data["stats"]["basic"]["comments"]["worst"]["text"] = 	Markup(markdown.markdown(user.data["stats"]["basic"]["comments"]["worst"]["text"])) \
																if user.data["stats"]["basic"]["comments"]["worst"]["text"] else None
	return render_template('user_profile.html', user=user, data=json.dumps(user.data))

def update_user():
	data=request.get_json()
	if not data:
		return "EMPTY"
	username = data["username"]
	user = User(
				#id=username,
				username=username,
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

