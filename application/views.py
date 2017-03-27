"""
views.py

URL route handlers

"""

import re
import json
import random
import logging
import math
import datetime
import time
from collections import Counter

import markdown
import httplib2
import requests
from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.api import search
from google.appengine.api import users
from flask import (
    request, render_template, url_for, redirect, abort, Markup, jsonify, make_response
)
from apiclient.discovery import build
from oauth2client.appengine import AppAssertionCredentials
from mapreduce import operation as op
from mapreduce import model
from mapreduce import mapreduce_pipeline
from google.appengine.runtime.apiproxy_errors import DeadlineExceededError
import pipeline

from application.decorators import admin_required
from application import app
from application.models import  (
    User, Feedback, ErrorLog, Subreddit, Category, CategoryTree,
    PredefinedCategorySuggestion, ManualCategorySuggestion,
    SubredditRelation, PreprocessedItem, SubredditRecommendationFeedback,
    SearchQuery, SubredditCategoryStage
)

class Bunch(object):
    """Simple unprotected bunch class."""
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

SAMPLE_TOPICS = [
    {
        "id":"reddit_music_metal",
        "caption": "Discuss metal music.",
        "icon": "reddit_music"
    },
    {
        "id":"reddit_hobbies-and-interests_languages",
        "caption": "Learn a new language.",
        "icon": "reddit_hobbies-and-interests_languages"
    },
    {
        "id":"reddit_sports_soccer",
        "caption": "Connect with soccer fans.",
        "icon": "reddit_sports_soccer"
    },
    {
        "id":"reddit_business_jobs-and-careers",
        "caption": "Get help with finding a job.",
        "icon": "reddit_business"
    },
    {
        "id":"reddit_entertainment_television",
        "caption": "Talk about your favorite TV shows.",
        "icon": "reddit_entertainment_television"
    },
    {
        "id":"reddit_lifestyle_food-and-beverages_cooking",
        "caption": "Learn how to cook.",
        "icon": "reddit_lifestyle_food-and-beverages_cooking"
    },
    {
        "id":"reddit_technology_programming",
        "caption": "Learn programming.",
        "icon": "reddit_technology_programming"
    },
    {
        "id":"reddit_hobbies-and-interests_outdoors_cycling",
        "caption": "Share your love for cycling.",
        "icon": "reddit_hobbies-and-interests_outdoors_cycling"
    },
]

MAX_RESULTS_PER_PAGE = 20
MAX_PAGES = 50
OPER_CHARACTERS = [":", "<", ">"]
STOP_WORDS = [
    "a", "an", "any", "are", "as", "at", "be", "but",
    "can", "do", "for", "from", "had", "has", "have",
    "i", "if", "in", "is", "it", "no", "of", "on",
    "so", "that", "the", "to"
]

HEADERS = {
    'User-Agent': 'SnoopSnoo v0.1 by /u/orionmelt'
}
SUBREDDIT_TYPES = {
    'public':0,
    'restricted':1,
    'private':2,
    'archived':3,
    None:4,
    'employees_only':5,
    'gold_restricted':6,
    'gold_only':6,
    'user':7
}
SUBMISSION_TYPES = {
    'any':0,
    'link':1,
    'self':2,
    None:3
}

def chunk(input_list, chunk_size):
    """Yield successive chunks from input list."""
    for i in xrange(0, len(input_list), chunk_size):
        yield input_list[i:i+chunk_size]

def uniq(seq):
    """Removes duplicates from a given sequence."""
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

def get_bq_service():
    """Builds and returns a BigQuery service."""
    app_credentials = AppAssertionCredentials(
        scope="https://www.googleapis.com/auth/bigquery"
    )
    http = app_credentials.authorize(httplib2.Http())
    return build("bigquery", "v2", http=http)

def bq_query(query, params=None, cache_key=None, cached=True):
    """Returns BigQuery results as a dictionary."""
    if not cache_key:
        cache_key = "bq_" + query
    results = memcache.get(cache_key)
    if not results or not cached:
        bigquery_service = get_bq_service()
        query_string = app.config["BQ_QUERIES"][query]
        if params:
            query_string = query_string % params
        query_response = None
        query_done = False
        while not query_done:
            try:
                query_data = {
                    "query": query_string,
                    "useQueryCache": cached
                }
                query_request = bigquery_service.jobs()
                query_response = query_request.query(
                    projectId=app.config["GOOGLE_CLOUD_PROJECT_ID"],
                    body=query_data
                ).execute()
                query_done = query_response["jobComplete"]
            except DeadlineExceededError:
                pass
        if not query_response or "rows" not in query_response:
            return []
        results = []
        for row in query_response["rows"]:
            result = {}
            for i, key in enumerate(query_response["schema"]["fields"]):
                value = {
                    "STRING": lambda x: x,
                    "INTEGER": lambda x: int(x) if x else 0,
                    "FLOAT": lambda x: float(x) if x else 0,
                    "BOOLEAN": lambda x: True if x == "true" else False,
                    "TIMESTAMP": lambda x: \
                        datetime.datetime.fromtimestamp(float(x)).strftime("%Y-%m-%d")
                }[key["type"]](row["f"][i]["v"])
                result[key["name"]] = value
            results.append(result)
        memcache.add(cache_key, results)
    return results

def get_subreddit(display_name_lower):
    """Returns a subreddit object given a subreddit name."""
    if not display_name_lower:
        return None
    sub = memcache.get("subreddit_" + display_name_lower)
    if sub:
        return sub
    else:
        sub = Subreddit.query(
            Subreddit.display_name_lower == display_name_lower
        ).get()
        if sub:
            memcache.add("subreddit_" + display_name_lower, sub)
            return sub
    return None

def get_all_subreddit_categories():
    """
    Returns a list of all subreddit categories that has already
    been precomputed.
    """
    all_subreddit_categories = memcache.get("all_subreddit_categories")

    if not all_subreddit_categories:
        prep_item = PreprocessedItem.get_by_id("all_subreddit_categories")
        if prep_item:
            all_subreddit_categories = json.loads(prep_item.data)
            memcache.add("all_subreddit_categories", all_subreddit_categories)

    return all_subreddit_categories

def get_subreddits_root():
    """Returns the category root tree."""
    root = memcache.get("subreddits_root")
    if not root:
        root = CategoryTree.get_by_id("reddit")
        memcache.add("subreddits_root", root)
    return root

def get_related_subreddits(subreddit_id, limit=5):
    """
    Returns a list of related subreddits (up to a certain given limit)
    for a given subreddit.
    """
    related_subreddits = memcache.get("related_" + subreddit_id)
    if not related_subreddits:
        related_target_ids = [
            ndb.Key("Subreddit", r.target) \
                for r in SubredditRelation.query(
                    SubredditRelation.source == subreddit_id
                ).order(-SubredditRelation.weight).fetch(limit)
        ]
        related_source_ids = [
            ndb.Key("Subreddit", r.source) for r in SubredditRelation.query(
                SubredditRelation.target == subreddit_id
            ).order(-SubredditRelation.weight).fetch(limit)
        ]
        related_subreddits = [
            x for x in ndb.get_multi(
                uniq(related_target_ids + related_source_ids)
            ) if x
        ]
        memcache.add("related_" + subreddit_id, related_subreddits)
    return related_subreddits

def get_recommended_subreddits(subreddits):
    """Returns a list of recommended subreddits given a list of subreddits."""
    input_subreddits = [
        x.lower() \
            for x in subreddits.split(",") \
                if re.match(r"^[\w]+$", x) is not None
    ]
    if not input_subreddits:
        return jsonify(recommended=[])
    recommended_subreddits = []
    s_keys = Subreddit.query(
        Subreddit.display_name_lower.IN(input_subreddits)
    ).fetch(keys_only=True)

    for s_key in s_keys:
        related = [
            item for item in [
                x.display_name \
                    for x in get_related_subreddits(s_key.id(), limit=5)
            ] if item.lower() not in input_subreddits
        ]
        recommended_subreddits.append(related)
    if recommended_subreddits:
        flattened_list = [
            item for sublist in recommended_subreddits for item in sublist
        ]
        counter = Counter(flattened_list)
        output_list = sorted(
            counter, key=lambda x: (-counter[x], flattened_list.index(x))
        )
        return jsonify(recommended=output_list)
    else:
        return jsonify(recommended=[])

def home():
    """Renders the site home page."""
    new_subs = []
    trending_subs = []

    prep_new_subs = PreprocessedItem.get_by_id("new_subs")
    if prep_new_subs:
        new_subs = json.loads(prep_new_subs.data)

    prep_trending_subs = PreprocessedItem.get_by_id("trending_subs")
    if prep_trending_subs:
        trending_subs = json.loads(prep_trending_subs.data)

    return render_template(
        "index.html",
        new_subs=new_subs,
        trending_subs=trending_subs
    )

def about():
    """Renders the site about page."""
    return render_template("about.html")

def reddit_history():
    """Renders the Nibble reddit history page."""
    return render_template("nibble/reddit_history.html")

def first_post():
    """Renders the Nibble first post page."""
    username = request.args.get("username") or None
    comment_id = request.args.get("comment_id") or None
    comment_subreddit = request.args.get("comment_subreddit") or None
    comment_link_id = request.args.get("comment_link_id") or None

    submission_id = request.args.get("submission_id") or None
    submission_subreddit = request.args.get("submission_subreddit") or None

    complete = request.args.get("complete") or None
    return render_template(
        "nibble/first_post.html",
        username=username,
        comment_id=comment_id,
        comment_subreddit=comment_subreddit,
        comment_link_id=comment_link_id,
        submission_id=submission_id,
        submission_subreddit=submission_subreddit,
        complete=complete
    )

def get_first_post():
    """Retrieves user's first comment/submission from BigQuery."""
    username = request.form["username"].lower().strip()
    post = bq_query("first_post", params=(username), cached=False)

    comment_id = post[0]["comment_id"] if len(post) and "comment_id" in post[0] else None
    comment_subreddit = post[0]["comment_subreddit"] \
        if len(post) and "comment_subreddit" in post[0] else None
    comment_link_id = post[0]["comment_link_id"] \
        if len(post) and "comment_link_id" in post[0] else None
    if comment_link_id:
        comment_link_id = comment_link_id[3:]

    submission_id = post[0]["submission_link_id"] \
        if len(post) and "submission_link_id" in post[0] else None
    submission_subreddit = post[0]["submission_subreddit"] \
        if len(post) and "submission_subreddit" in post[0] else None
    return redirect(
        url_for(
            "first_post",
            username=username,
            comment_id=comment_id,
            comment_subreddit=comment_subreddit,
            comment_link_id=comment_link_id,
            submission_id=submission_id,
            submission_subreddit=submission_subreddit,
            complete="1"
        )
    )

def random_user():
    """Redirects to a random user profile page."""
    user = ndb.Key("User", random.randrange(math.pow(2, 52) - 1))
    keys = User.query(User.key > user).fetch(1000, keys_only=True)
    if not keys:
        User.query(User.key < user).fetch(1000, keys_only=True)
    key = random.choice(keys)
    return redirect("/u/" + key.get().username)

def check_user(username):
    """Checks if a user with given username already exists."""
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
    """Renders the user profile page given their username."""
    user = User.query(User.username_lower == username.lower()).get()
    if not user:
        user = User.query(User.username == username).get()
    if not user:
        return render_template("blank_profile.html", username=username), 404

    user.data["summary"]["comments"]["best"]["text"] = \
        Markup(
            markdown.markdown(user.data["summary"]["comments"]["best"]["text"])
        ) if user.data["summary"]["comments"]["best"]["text"] else None

    user.data["summary"]["comments"]["worst"]["text"] = \
        Markup(
            markdown.markdown(
                user.data["summary"]["comments"]["worst"]["text"]
            )
        ) if user.data["summary"]["comments"]["worst"]["text"] else None

    all_subreddit_categories = get_all_subreddit_categories()

    user_averages = bq_query("user_averages")[0]
    return render_template(
        "user_profile.html",
        user=user,
        data=json.dumps(user.data),
        all_subreddit_categories=all_subreddit_categories,
        user_averages=json.dumps(user_averages)
    )

def get_user_data(username):
    """Returns user data."""
    user = User.query(User.username_lower == username.lower()).get()
    if user:
        user.data["metadata"]["last_updated"]=user.last_updated
    return jsonify(data=user.data) if user else jsonify(error=404)

def update_user():
    """Updates user data given the data in a POST request."""
    data = request.get_json()
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
            id=data["metadata"]["reddit_id"],
            username=username,
            data_version=data_version,
            data=data
        )
        user.put()
    return "OK"

def save_synopsis_feedback():
    """Persists synopsis feedback given in a GET request."""
    username = request.args.get("u")
    data_key = request.args.get("k")
    data_value = request.args.get("v")
    feedback_value = request.args.get("f") == "1"
    synopsis_feedback = Feedback(
        username=username,
        data_key=data_key,
        data_value=data_value,
        feedback=feedback_value
    )
    synopsis_feedback.put()
    return "OK"

def save_sub_reco_feedback():
    """Persists subreddit recommendation feedback given in a GET request."""
    username = request.args.get("u")
    input_subreddits = request.args.get("i")
    recommended_subreddit = request.args.get("o")
    feedback_value = request.args.get("f") == "1"
    sub_reco_feedback = SubredditRecommendationFeedback(
        username=username,
        input_subreddits=input_subreddits,
        recommended_subreddit=recommended_subreddit,
        feedback=feedback_value
    )
    sub_reco_feedback.put()
    return "OK"

def save_error():
    """Saves error message given in a GET request."""
    username = request.args.get("u")
    error_type = request.args.get("t")
    error_message = request.args.get("m")
    error = ErrorLog(
        username=username,
        error_type=error_type,
        error_message=error_message
    )
    error.put()
    return "OK"

def save_sub_category_suggestion():
    """Persists subreddit category suggestion by users."""
    category_ids = request.form.getlist("category_id")
    subreddit_names = request.form.getlist("subreddit_name")
    suggested_categories = request.form.getlist("suggested_category")

    predefined_suggestions = []
    manual_suggestions = []

    for i, category_id in enumerate(category_ids):
        if not (category_id or suggested_categories[i]):
            continue

        subreddit_name = subreddit_names[i]
        suggested_category = suggested_categories[i]

        if not suggested_category:
            category_suggestion = PredefinedCategorySuggestion(
                subreddit_display_name=subreddit_name,
                category_id=category_id
            )
            predefined_suggestions.append(category_suggestion)
        else:
            category_suggestion = ManualCategorySuggestion(
                subreddit_display_name=subreddit_name,
                category_id=category_id,
                suggested_category=suggested_category
            )
            manual_suggestions.append(category_suggestion)
    if predefined_suggestions:
        ndb.put_multi(predefined_suggestions)
    if manual_suggestions:
        ndb.put_multi(manual_suggestions)
    return "OK"

@admin_required
def stage_sub_category():
    """Saves subreddit category set by admin to stage."""
    category_id = request.form.get("category_id")
    subreddit_id = request.form.get("subreddit_id")
    user = users.get_current_user()
    user_id = user.nickname()
    stage_entry = SubredditCategoryStage(
        subreddit_id=subreddit_id,
        category_id=category_id,
        user_id=user_id
    )
    stage_entry.put()
    return "OK"

def subreddits_home():
    """Renders subreddits directory home page."""
    root = get_subreddits_root()

    new_subs = None
    trending_subs = None
    growing_subs = None

    prep_new_subs = PreprocessedItem.get_by_id("new_subs")
    if prep_new_subs:
        new_subs = json.loads(prep_new_subs.data)
    prep_trending_subs = PreprocessedItem.get_by_id("trending_subs")
    if prep_trending_subs:
        trending_subs = json.loads(prep_trending_subs.data)
    prep_growing_subs = PreprocessedItem.get_by_id("growing_subs")
    if prep_growing_subs:
        growing_subs = json.loads(prep_growing_subs.data)

    return render_template(
        "subreddits_home.html",
        root=json.loads(root.data),
        subreddit_count=root.subreddit_count,
        last_updated=root.last_updated,
        intro_items=random.sample(SAMPLE_TOPICS, 3),
        growing_subs=growing_subs,
        new_subs=new_subs,
        trending_subs=trending_subs
    )

def subreddits_category(level1, level2=None, level3=None):
    """
    Renders particular subreddits category page
    given a category of up to 3 levels.
    """
    if level1 == "adult":
        url = url_for(
            "subreddits_category",
            level1="adult-and-nsfw",
            level2=level2,
            level3=level3
        )
        if request.query_string:
            url += "?" + request.query_string
        return redirect(url, code=301)
    category_id = "reddit_" + level1.lower()
    breadcrumbs_ids = [category_id]
    if level2:
        category_id += "_" + level2.lower()
        breadcrumbs_ids.append(category_id)
    if level3:
        category_id += "_" + level3.lower()
        breadcrumbs_ids.append(category_id)

    category = Category.get_by_id(category_id)

    if not category:
        abort(404)

    ct_object = CategoryTree.get_by_id(category_id)
    category_tree = [
        x for x in json.loads(ct_object.data)["children"] if "children" in x
    ]
    breadcrumbs = [Category.get_by_id(x) for x in breadcrumbs_ids]

    cursor = request.args.get("c")
    is_prev = True if request.args.get("p") else False

    subreddits, prev_bookmark, next_bookmark = return_query_page(
        query_class=Subreddit,
        bookmark=cursor,
        is_prev=is_prev,
        equality_filters={"parent_id": category_id},
        orders={"subscribers": "-"}
    )

    if cursor and not subreddits:
        abort(404)

    trending_subs_in_cat = None
    prep_trending_subs_in_cat = PreprocessedItem.get_by_id("trending_%s" % category_id)
    if prep_trending_subs_in_cat:
        trending_subs_in_cat = json.loads(prep_trending_subs_in_cat.data)

    return render_template(
        "subreddits_category.html",
        subreddits=subreddits,
        category=category,
        cat_tree=category_tree,
        breadcrumbs=breadcrumbs,
        prev=prev_bookmark,
        next=next_bookmark,
        all_subreddit_categories=get_all_subreddit_categories(),
        subreddit_count=ct_object.subreddit_count,
        root=json.loads(get_subreddits_root().data),
        trending_subs_in_cat=trending_subs_in_cat
    )

def subreddit(subreddit_name):
    """Renders individual subreddit page."""
    root = get_subreddits_root()
    subreddit_name = subreddit_name.lower()
    sub = get_subreddit(subreddit_name)
    is_admin = users.is_current_user_admin()
    if not sub:
        return render_template(
            "subreddit_not_found.html",
            subreddit=subreddit_name
        ), 404

    breadcrumbs = []
    for i, _ in enumerate(sub.parent_id.split("_")):
        breadcrumbs.append(
            Category.get_by_id("_".join(sub.parent_id.split("_")[:i+1]))
        )

    related_subreddits = get_related_subreddits(sub.key.id())

    all_subreddit_categories = get_all_subreddit_categories()

    trending_subs_in_cat = None
    prep_trending_subs_in_cat = PreprocessedItem.get_by_id("trending_%s" % sub.parent_id)
    if prep_trending_subs_in_cat:
        trending_subs_in_cat = json.loads(prep_trending_subs_in_cat.data)

    return render_template(
        "subreddit.html",
        subreddit=sub,
        breadcrumbs=breadcrumbs[1:],
        all_subreddit_categories=all_subreddit_categories,
        related_subreddits=related_subreddits,
        root=json.loads(root.data),
        trending_subs_in_cat=trending_subs_in_cat,
        is_admin=is_admin
    )

def subreddit_category(subreddit_name):
    """Returns subreddit category data as JSON."""
    root = get_subreddits_root()
    subreddit_name = subreddit_name.lower()
    sub = get_subreddit(subreddit_name)
    if not sub:
        return jsonify(error=404)
    breadcrumbs = []
    for i, _ in enumerate(sub.parent_id.split("_")):
        breadcrumbs.append(
            Category.get_by_id("_".join(sub.parent_id.split("_")[:i+1])).display_name
        )
    return jsonify(categories=breadcrumbs[1:])


def subreddit_frontpage():
    """Renders frontpage preview for given subreddit."""
    over18 = int(request.args.get("over18"))
    age_confirmed = int(request.args.get("age_confirmed"))
    data = request.get_json()
    return render_template(
        "subreddit_frontpage.html",
        front_page=data,
        over18=over18,
        age_confirmed=age_confirmed
    )

def search_subreddits():
    """Returns subreddit search results given query string in a GET request."""
    search_query = request.args.get("q")
    if not search_query:
        return redirect(url_for("subreddits_home"))

    search_query = search_query.strip()
    search_query = re.sub(r"\s*([\:\<\>])\s*", r"\1", search_query)
    query_string = re.sub(r"[~\(\)]", "", search_query)
    # Remove /r/ from query string
    query_string = re.sub(r"\s?\/?r\/\s?", r"", query_string)
    query_string = re.sub(r"\+", " AND ", query_string)
    query_string = re.sub(r"\-", " NOT ", query_string)

    query_string = " ".join(
        [x for x in query_string.split(" ") \
            if not any(o in x for o in OPER_CHARACTERS)]
    )

    query_string = " ".join(
        [x for x in query_string.split(" ") if x.lower() not in STOP_WORDS]
    )

    query_filters = " " + " ".join(
        [x for x in search_query.split(" ") \
            if any(o in x for o in OPER_CHARACTERS)]
    )

    page_number = request.args.get("page")
    if page_number and page_number.isnumeric():
        page_number = int(page_number)
        page_number = page_number if page_number <= MAX_PAGES else MAX_PAGES
    else:
        page_number = 1

    try:
        results = []
        subreddits = []
        index = search.Index(name="subreddits_search")

        if (not page_number or page_number == 1) and len(query_string.strip()):
            SearchQuery(
                kind=0,
                query_text=search_query,
                country=request.headers.get("X-AppEngine-Country"),
                region=request.headers.get("X-AppEngine-Region"),
                city=request.headers.get("X-AppEngine-City"),
                latlong=request.headers.get("X-AppEngine-CityLatLong"),
                remote_addr=request.remote_addr
            ).put()
            name_result = index.search(search.Query(
                query_string=("display_name:(%s)" % " ".join(
                    ["~"+x if x.lower() not in ["and", "not", "or"] else x \
                        for x in query_string.split(" ") if x]
                )) + " OR " + (
                    "display_name:%s" % re.sub(" ", "", query_string)
                )  + " OR " + (
                    "display_name:%s" % re.sub(" ", "_", query_string)
                ) + query_filters,
                options=search.QueryOptions(limit=5)
            ))
            results += name_result.results

            title_result = index.search(search.Query(
                query_string=("title:(%s)" % " ".join(
                    ["~"+x if x.lower() not in ["and", "not", "or"] else x \
                        for x in query_string.split(" ") if x]
                )) + " OR " + (
                    "title:%s" % re.sub(" ", "", query_string)
                )  + " OR " + (
                    "title:%s" % re.sub(" ", "_", query_string)
                ) + query_filters,
                options=search.QueryOptions(limit=5)
            ))
            results += title_result.results

        if not page_number or page_number == 1:
            offset = 0
        else:
            offset = (page_number-1) * MAX_RESULTS_PER_PAGE

        other_result = index.search(search.Query(
            query_string=" ".join(
                ["~"+x if x.lower() not in ["and", "not", "or"] else x \
                        for x in query_string.split(" ") if x]
            ) + query_filters,
            options=search.QueryOptions(offset=offset)
        ))
        results += other_result.results

        for item in results:
            display_name = [
                x.value for x in item.fields if x.name == "display_name"
            ][0]
            if display_name in [x.display_name for x in subreddits]:
                continue
            title = [
                x.value for x in item.fields if x.name == "title"
            ][0]
            public_description = [
                x.value for x in item.fields if x.name == "public_description"
            ][0]
            subscribers = [
                x.value for x in item.fields if x.name == "subscribers"
            ][0]
            created_utc = [
                x.value for x in item.fields if x.name == "created"
            ][0]
            over18 = True if [
                x.value for x in item.fields if x.name == "over18"
            ][0] == "true" else False
            subreddit_type = [
                x.value for x in item.fields if x.name == "subreddit_type"
            ][0]
            subreddits.append(
                Bunch(
                    display_name=display_name,
                    title=title,
                    public_description=public_description,
                    subscribers=subscribers,
                    created_utc=created_utc,
                    over18=over18,
                    subreddit_type=subreddit_type
                )
            )

        return render_template(
            "subreddit_search_results.html",
            search_query=search_query,
            result=Bunch(
                subreddits=subreddits,
                page_number=page_number,
                prev_page=(page_number-1) if page_number > 1 else None,
                next_page=(page_number+1) if (
                    len(other_result.results) == 20 and \
                    page_number < MAX_PAGES
                ) else None
            )
        )
    except search.Error:
        logging.exception("Search error")
        return render_template(
            "subreddit_search_results.html",
            search_query=search_query,
            result=Bunch(
                subreddits=[],
                page_number=1,
                prev_page=None,
                next_page=None
            )
        )

def base36encode(number, alphabet="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    """Converts integer to base36 string."""
    if not isinstance(number, (int)):
        raise TypeError('number must be an integer')
    base36 = ''
    sign = ''
    if number < 0:
        sign = '-'
        number = -number
    if 0 <= number < len(alphabet):
        return sign + alphabet[number]
    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36
    return (sign + base36).lower()

def base36decode(number):
    """Converts base36 string to integer."""
    return int(number, 36)

def b36(i):
    """Handles base36 encode/decode."""
    if isinstance(i, int):
        return base36encode(i)
    if isinstance(i, str):
        return base36decode(i)

def add_new_subs():
    """Adds newly created subreddits to the datastore."""
    oldest = Subreddit.query().order(-Subreddit.created_utc).get()
    index = search.Index(name="subreddits_search")

    response = requests.get("https://www.reddit.com/subreddits/new.json?limit=1", headers=HEADERS)
    response_json = response.json()
    newest_id = str(response_json["data"]["children"][0]["data"]["id"])
    num_nsfw = 0
    num_other = 0
    time.sleep(10)

    for ids in chunk(range(b36(oldest.key.id())+1, b36(newest_id)+1), 100):
        url = "https://www.reddit.com/api/info.json?id=" + ",".join(
            ["t5_" + b36(x) for x in ids]
        )
        ndb_subs = []
        search_docs = []
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            raise Exception("Invalid response: HTTP %d" % response.status_code)
        try:
            response_json = response.json()
        except ValueError:
            continue
        for sub in response_json["data"]["children"]:
            ndb_sub = Subreddit(
                id=sub["data"]["id"],
                subreddit_id=sub["data"]["id"],
                display_name=sub["data"]["display_name"],
                title=sub["data"]["title"],
                public_description=sub["data"]["public_description"],
                description_html=sub["data"]["description_html"],
                subreddit_type=SUBREDDIT_TYPES[sub["data"]["subreddit_type"]],
                submission_type=SUBMISSION_TYPES[sub["data"]["submission_type"]],
                created_utc=datetime.datetime.fromtimestamp(sub["data"]["created_utc"]),
                subscribers=sub["data"]["subscribers"],
                over18=sub["data"]["over18"],
                parent_id="reddit_adult-and-nsfw" if sub["data"]["over18"] else "reddit_other"
            )
            ndb_subs.append(ndb_sub)

            if ndb_sub.over18:
                num_nsfw += 1
            else:
                num_other += 1

            fields = [
                search.TextField(name='display_name', value=ndb_sub.display_name),
                search.TextField(name='title', value=ndb_sub.title),
                search.TextField(name='public_description', value=ndb_sub.public_description),
                search.NumberField(name='subscribers', value=ndb_sub.subscribers or 0),
                search.DateField(name='created', value=ndb_sub.created_utc),
                search.AtomField(name='over18', value="true" if ndb_sub.over18 else "false"),
                search.NumberField(name='subreddit_type', value=ndb_sub.subreddit_type),
                search.NumberField(name='submission_type', value=ndb_sub.submission_type),
                search.TextField(
                    name='topic',
                    value="Adult and NSFW" if ndb_sub.over18 else "Other"
                )
            ]
            doc = search.Document(
                doc_id=ndb_sub.key.id(),
                fields=fields,
                rank=ndb_sub.subscribers if ndb_sub.subscribers > 0 else 1
            )
            search_docs.append(doc)

        ndb.put_multi(ndb_subs)
        index.put(search_docs)
        time.sleep(10)

    nsfw_category = Category.get_by_id("reddit_adult-and-nsfw")
    nsfw_category.subreddit_count += num_nsfw
    nsfw_category.total_subreddit_count += num_nsfw
    nsfw_category.put()
    other_category = Category.get_by_id("reddit_other")
    other_category.subreddit_count += num_other
    other_category.total_subreddit_count += num_other
    other_category.put()
    filters = [
        ("subreddit_id", ">", oldest.key.id()),
        ("subreddit_id", "<=", newest_id),
    ]
    export_subreddits_handler(filters=filters)
    update_total_count("reddit")
    update_category_tree("reddit")
    return "Done"

def count_subreddits_handler(sub):
    """MapReduce handler for counting subreddits by category."""
    yield op.counters.Increment(sub.parent_id)

def count_subreddits_callback():
    """MapReduce callback for counting subreddits by category."""
    mapreduce_id = request.headers.get("Mapreduce-Id")
    state = model.MapreduceState.get_by_key_name(mapreduce_id)
    for category, count in state.counters_map.to_dict().iteritems():
        if not category.startswith("reddit"):
            continue
        ndb_category = Category.get_by_id(category)
        ndb_category.subreddit_count = count
        ndb_category.put()
    update_total_count("reddit")
    update_category_tree("reddit")
    return "Done"

def update_total_count(node="reddit"):
    """Updates total subreddit count for given category and its children."""
    children = Category.query(Category.parent_id == node).fetch()
    ndb_category = Category.get_by_id(node)
    count = ndb_category.subreddit_count
    for child in children:
        count += update_total_count(child.key.id())
    ndb_category.total_subreddit_count = count
    ndb_category.put()
    return count

def update_category_tree(node="reddit"):
    """Updates category tree for given category and its children."""
    category = Category.get_by_id(node)
    child_cats = Category.query(Category.parent_id == node).fetch()
    child_cats = sorted(
        child_cats,
        key=lambda x: x.display_name \
            if x.display_name.lower() not in ["other"] else "z"
    )
    children = []
    if node != "reddit":
        child_subs = Subreddit.query(
            Subreddit.parent_id == node
        ).order(-Subreddit.subscribers).fetch(5)
        for child_sub in child_subs:
            children.append({"id": child_sub.key.id(), "display_name": child_sub.display_name})
        children.append({"id": "more_subs", "count": category.subreddit_count - 5})
    for child_cat in child_cats:
        children.append(update_category_tree(child_cat.key.id()))
    data = {
        "id": category.key.id(),
        "display_name": category.display_name,
        "children": children
    }
    cat_tree = CategoryTree(
        id=category.key.id(),
        data=json.dumps(data),
        subreddit_count=category.total_subreddit_count
    )
    cat_tree.put()
    return data

def process_sub_category_stage():
    """Processes staging entries and updates categories."""
    from_ts = datetime.datetime.now()
    index = search.Index(name="subreddits_search")
    stage_entries = SubredditCategoryStage.query().order(
        SubredditCategoryStage.log_date
    ).fetch(200)
    if not stage_entries:
        return "Done"
    subs = []
    processed = []
    docs = []
    categories = Category.query().fetch()
    for stage_entry in stage_entries:
        if stage_entry.subreddit_id in processed:
            continue
        sub = Subreddit.get_by_id(stage_entry.subreddit_id)
        if not sub:
            continue
        old_category = [x for x in categories if x.key.id() == sub.parent_id][0]
        new_category = [
            x for x in categories if x.key.id() == stage_entry.category_id
        ][0]
        old_category.subreddit_count -= 1
        new_category.subreddit_count += 1
        sub.parent_id = stage_entry.category_id
        subs.append(sub)
        processed.append(stage_entry.subreddit_id)
        doc = index.get(stage_entry.subreddit_id)
        if not doc:
            continue
        doc_fields = [f for f in doc.fields if f.name != "topic"]
        search_topics = []
        current_parent_id = sub.parent_id
        while current_parent_id != "reddit":
            cat = [x for x in categories if x.key.id() == current_parent_id][0]
            search_topics.append(
                search.TextField(name="topic", value=cat.display_name)
            )
            current_parent_id = cat.parent_id
        doc_fields += search_topics
        doc = search.Document(
            doc_id=doc.doc_id,
            fields=doc_fields,
            rank=sub.subscribers if sub.subscribers > 0 else 1
        )
        docs.append(doc)
    ndb.put_multi(subs)
    ndb.put_multi(categories)
    ndb.delete_multi([x.key for x in stage_entries])
    index.put(docs)
    update_total_count("reddit")
    update_category_tree("reddit")
    filters = [
        ("last_updated", ">", from_ts),
        ("last_updated", "<=", datetime.datetime.now()),
    ]
    export_subreddits_handler(filters=filters)
    return "Done"

class ExportSubredditsPipeline(pipeline.Pipeline):
    """A pipeline that iterates through Subreddit entities."""
    def run(self, filters=None):
        """Iterates through Subreddit entities and writes to GCS files."""
        output = yield mapreduce_pipeline.MapperPipeline(
            "ExportSubredditsPipeline",
            "application.views.export_subreddits_map",
            "mapreduce.input_readers.DatastoreInputReader",
            output_writer_spec="mapreduce.output_writers.GoogleCloudStorageOutputWriter",
            params={
                "input_reader": {
                    "entity_kind": "application.models.Subreddit",
                    "filters": filters or []
                },
                "output_writer": {
                    "bucket_name": app.config["GCS_BUCKET_NAME"]
                }
            },
            shards=128
        )
        yield ImportSubredditsIntoBigQuery(output)

class ImportSubredditsIntoBigQuery(pipeline.Pipeline):
    """A pipeline that imports Subreddit entities into BigQuery."""
    def run(self, subreddits_files):
        """Import Subreddit entities from GCS into BigQuery."""
        bigquery_service = get_bq_service()
        jobs = bigquery_service.jobs()
        table_name = "_subreddits"
        files = [str("gs:/" + f) for f in subreddits_files]
        result = jobs.insert(
            projectId=app.config["GOOGLE_CLOUD_PROJECT_ID"],
            body={
                "projectId": app.config["GOOGLE_CLOUD_PROJECT_ID"],
                "configuration": {
                    "load": {
                        "quote": "",
                        "sourceUris": files,
                        "schema": {
                            "fields": [
                                {
                                    "name": "log_date",
                                    "type": "TIMESTAMP"
                                },
                                {
                                    "name": "subreddit_id",
                                    "type": "STRING"
                                },
                                {
                                    "name": "display_name",
                                    "type": "STRING"
                                },
                                {
                                    "name": "created_utc",
                                    "type": "TIMESTAMP"
                                },
                                {
                                    "name": "over18",
                                    "type": "BOOLEAN"
                                },
                                {
                                    "name": "parent_id",
                                    "type": "STRING"
                                }
                            ]
                        },
                        "destinationTable": {
                            "projectId": app.config["GOOGLE_CLOUD_PROJECT_ID"],
                            "datasetId": app.config["BIGQUERY_DATASET_ID"],
                            "tableId": table_name
                        }
                    }
                }

            }
        ).execute()
        logging.info(result)

def export_subreddits_map(sub):
    """Map function for exporting Subreddit entities."""
    today = datetime.datetime.combine(datetime.date.today(), datetime.datetime.now().time())
    row = "%s,%s,%s,%s,%s,%s\n" % (
        today.strftime("%Y-%m-%d %H:%S"),
        str(sub.key.id()),
        sub.display_name.encode("ascii", "ignore").strip(),
        sub.created_utc.strftime("%Y-%m-%d %H:%M"),
        1 if sub.over18 else 0,
        str(sub.parent_id)
    )
    yield row

def export_subreddits_handler(filters=None):
    """Handler function for exporting Subreddit entities."""
    mr_pipeline = ExportSubredditsPipeline(filters)
    mr_pipeline.start()
    path = mr_pipeline.base_path + "/status?root=" + mr_pipeline.pipeline_id
    return "Kicked off job: %s" % path

class ExportSynopsisFeedbackPipeline(pipeline.Pipeline):
    """A pipeline that iterates through Feedback entities."""
    def run(self, start_ts, end_ts):
        """Iterates through Feedback entities and writes to GCS files."""
        output = yield mapreduce_pipeline.MapperPipeline(
            "ExportSynopsisFeedbackPipeline",
            "application.views.export_synopsis_feedback_map",
            "mapreduce.input_readers.DatastoreInputReader",
            output_writer_spec="mapreduce.output_writers.GoogleCloudStorageOutputWriter",
            params={
                "input_reader": {
                    "entity_kind": "application.models.Feedback",
                    "filters": \
                        [
                            ("log_date", ">=", start_ts),
                            ("log_date", "<", end_ts)
                        ]
                },
                "output_writer": {
                    "bucket_name": app.config["GCS_BUCKET_NAME"],
                }
            },
            shards=128
        )
        yield ImportSynopsisFeedbackIntoBigQuery(output)

class ImportSynopsisFeedbackIntoBigQuery(pipeline.Pipeline):
    """A pipeline that imports Feedback entities into BigQuery."""
    def run(self, feedback_files):
        """Import Feedback entities from GCS into BigQuery."""
        bigquery_service = get_bq_service()
        jobs = bigquery_service.jobs()
        table_name = "_synopsis_feedback"
        files = [str("gs:/" + f) for f in feedback_files]
        result = jobs.insert(
            projectId=app.config["GOOGLE_CLOUD_PROJECT_ID"],
            body={
                "projectId": app.config["GOOGLE_CLOUD_PROJECT_ID"],
                "configuration": {
                    "load": {
                        "quote": "",
                        "sourceUris": files,
                        "schema": {
                            "fields": [
                                {
                                    "name": "log_date",
                                    "type": "TIMESTAMP"
                                },
                                {
                                    "name": "username_lower",
                                    "type": "STRING"
                                },
                                {
                                    "name": "data_key",
                                    "type": "STRING"
                                },
                                {
                                    "name": "data_value",
                                    "type": "STRING"
                                },
                                {
                                    "name": "feedback",
                                    "type": "BOOLEAN"
                                }
                            ]
                        },
                        "destinationTable": {
                            "projectId": app.config["GOOGLE_CLOUD_PROJECT_ID"],
                            "datasetId": app.config["BIGQUERY_DATASET_ID"],
                            "tableId": table_name
                        }
                    }
                }

            }
        ).execute()
        logging.info(result)

def export_synopsis_feedback_map(feedback):
    """Map function for exporting Feedback entities."""
    row = "%s,%s,%s,%s,%s\n" % (
        feedback.log_date.strftime("%Y-%m-%d %H:%M"),
        feedback.username.encode("ascii", "ignore").lower() if feedback.username else "",
        feedback.data_key.encode("ascii", "ignore") if feedback.data_key else "",
        feedback.data_value.encode("ascii", "ignore") if feedback.data_value else "",
        1 if feedback.feedback else 0
    )
    yield row

def export_synopsis_feedback_handler():
    """Handler function for exporting Feedback entities."""
    today = datetime.datetime.combine(datetime.date.today(), datetime.time())
    yesterday = today - datetime.timedelta(hours=24)
    mr_pipeline = ExportSynopsisFeedbackPipeline(yesterday, today)
    mr_pipeline.start()
    path = mr_pipeline.base_path + "/status?root=" + mr_pipeline.pipeline_id
    return "Kicked off job: %s" % path

class ExportPredefinedCategorySuggestionPipeline(pipeline.Pipeline):
    """A pipeline that iterates through PredefinedCategorySuggestion entities."""
    def run(self, start_ts, end_ts):
        """Iterates through PredefinedCategorySuggestion entities and writes to GCS files."""
        output = yield mapreduce_pipeline.MapperPipeline(
            "ExportPredefinedCategorySuggestionPipeline",
            "application.views.export_predefined_category_suggestion_map",
            "mapreduce.input_readers.DatastoreInputReader",
            output_writer_spec="mapreduce.output_writers.GoogleCloudStorageOutputWriter",
            params={
                "input_reader": {
                    "entity_kind": "application.models.PredefinedCategorySuggestion",
                    "filters": \
                        [
                            ("log_date", ">=", start_ts),
                            ("log_date", "<", end_ts)
                        ]
                },
                "output_writer": {
                    "bucket_name": app.config["GCS_BUCKET_NAME"],
                }
            },
            shards=128
        )
        yield ImportPredefinedCategorySuggestionIntoBigQuery(output)

class ImportPredefinedCategorySuggestionIntoBigQuery(pipeline.Pipeline):
    """A pipeline that imports PredefinedCategorySuggestion entities into BigQuery."""
    def run(self, category_suggestion_files):
        """Import PredefinedCategorySuggestion entities from GCS into BigQuery."""
        bigquery_service = get_bq_service()
        jobs = bigquery_service.jobs()
        table_name = "_predefined_suggestions"
        files = [str("gs:/" + f) for f in category_suggestion_files]
        result = jobs.insert(
            projectId=app.config["GOOGLE_CLOUD_PROJECT_ID"],
            body={
                "projectId": app.config["GOOGLE_CLOUD_PROJECT_ID"],
                "configuration": {
                    "load": {
                        "quote": "",
                        "sourceUris": files,
                        "schema": {
                            "fields": [
                                {
                                    "name": "log_date",
                                    "type": "TIMESTAMP"
                                },
                                {
                                    "name": "display_name_lower",
                                    "type": "STRING"
                                },
                                {
                                    "name": "category_id",
                                    "type": "STRING"
                                }
                            ]
                        },
                        "destinationTable": {
                            "projectId": app.config["GOOGLE_CLOUD_PROJECT_ID"],
                            "datasetId": app.config["BIGQUERY_DATASET_ID"],
                            "tableId": table_name
                        }
                    }
                }

            }
        ).execute()
        logging.info(result)

def export_predefined_category_suggestion_map(suggestion):
    """Map function for exporting PredefinedCategorySuggestion entities."""
    row = "%s,%s,%s\n" % (
        suggestion.log_date.strftime("%Y-%m-%d %H:%M"),
        str(suggestion.subreddit_display_name_lower),
        str(suggestion.category_id),
    )
    yield row

def export_predefined_category_suggestion_handler():
    """Handler function for exporting PredefinedCategorySuggestion entities."""
    today = datetime.datetime.combine(datetime.date.today(), datetime.time())
    yesterday = today - datetime.timedelta(hours=24)
    mr_pipeline = ExportPredefinedCategorySuggestionPipeline(yesterday, today)
    mr_pipeline.start()
    path = mr_pipeline.base_path + "/status?root=" + mr_pipeline.pipeline_id
    return "Kicked off job: %s" % path

class ExportManualCategorySuggestionPipeline(pipeline.Pipeline):
    """A pipeline that iterates through ManualCategorySuggestion entities."""
    def run(self, start_ts, end_ts):
        """Iterates through ManualCategorySuggestion entities and writes to GCS files."""
        output = yield mapreduce_pipeline.MapperPipeline(
            "ExportManualCategorySuggestionPipeline",
            "application.views.export_manual_category_suggestion_map",
            "mapreduce.input_readers.DatastoreInputReader",
            output_writer_spec="mapreduce.output_writers.GoogleCloudStorageOutputWriter",
            params={
                "input_reader": {
                    "entity_kind": "application.models.ManualCategorySuggestion",
                    "filters": \
                        [
                            ("log_date", ">=", start_ts),
                            ("log_date", "<", end_ts)
                        ]
                },
                "output_writer": {
                    "bucket_name": app.config["GCS_BUCKET_NAME"],
                }
            },
            shards=128
        )
        yield ImportManualCategorySuggestionIntoBigQuery(output)

class ImportManualCategorySuggestionIntoBigQuery(pipeline.Pipeline):
    """A pipeline that imports ManualCategorySuggestion entities into BigQuery."""
    def run(self, category_suggestion_files):
        """Import ManualCategorySuggestion entities from GCS into BigQuery."""
        bigquery_service = get_bq_service()
        jobs = bigquery_service.jobs()
        table_name = "_manual_suggestions"
        files = [str("gs:/" + f) for f in category_suggestion_files]
        result = jobs.insert(
            projectId=app.config["GOOGLE_CLOUD_PROJECT_ID"],
            body={
                "projectId": app.config["GOOGLE_CLOUD_PROJECT_ID"],
                "configuration": {
                    "load": {
                        "sourceUris": files,
                        "schema": {
                            "fields": [
                                {
                                    "name": "log_date",
                                    "type": "TIMESTAMP"
                                },
                                {
                                    "name": "display_name_lower",
                                    "type": "STRING"
                                },
                                {
                                    "name": "category_id",
                                    "type": "STRING"
                                },
                                {
                                    "name": "suggested_category",
                                    "type": "STRING"
                                }
                            ]
                        },
                        "destinationTable": {
                            "projectId": app.config["GOOGLE_CLOUD_PROJECT_ID"],
                            "datasetId": app.config["BIGQUERY_DATASET_ID"],
                            "tableId": table_name
                        }
                    }
                }

            }
        ).execute()
        logging.info(result)

def export_manual_category_suggestion_map(suggestion):
    """Map function for exporting ManualCategorySuggestion entities."""
    suggested_category = suggestion.suggested_category.encode("ascii", "ignore").strip() \
        if suggestion.suggested_category else ""
    suggested_category = suggested_category.replace("\"", "'")
    row = "%s,%s,%s,\"%s\"\n" % (
        suggestion.log_date.strftime("%Y-%m-%d %H:%M"),
        str(suggestion.subreddit_display_name_lower),
        str(suggestion.category_id) if suggestion.category_id else "",
        suggested_category
    )
    yield row

def export_manual_category_suggestion_handler():
    """Handler function for exporting ManualCategorySuggestion entities."""
    today = datetime.datetime.combine(datetime.date.today(), datetime.time())
    yesterday = today - datetime.timedelta(hours=24)
    mr_pipeline = ExportManualCategorySuggestionPipeline(yesterday, today)
    mr_pipeline.start()
    path = mr_pipeline.base_path + "/status?root=" + mr_pipeline.pipeline_id
    return "Kicked off job: %s" % path

class ExportUserSummaryPipeline(pipeline.Pipeline):
    """A pipeline that iterates through User entities."""
    def run(self, start_ts, end_ts):
        """Iterates through User entities and writes to GCS files."""
        output = yield mapreduce_pipeline.MapperPipeline(
            "ExportUserSummaryPipeline",
            "application.views.export_user_summary_map",
            "mapreduce.input_readers.DatastoreInputReader",
            output_writer_spec="mapreduce.output_writers.GoogleCloudStorageOutputWriter",
            params={
                "input_reader": {
                    "entity_kind": "application.models.User",
                    "filters": \
                        [
                            ("last_updated", ">=", start_ts),
                            ("last_updated", "<", end_ts)
                        ]
                },
                "output_writer": {
                    "bucket_name": app.config["GCS_BUCKET_NAME"],
                }
            },
            shards=128
        )
        yield ImportUserSummaryIntoBigQuery(output)

class ImportUserSummaryIntoBigQuery(pipeline.Pipeline):
    """A pipeline that imports User entities into BigQuery."""
    def run(self, user_summary_files):
        """Import Feedback entities from GCS into BigQuery."""
        bigquery_service = get_bq_service()
        jobs = bigquery_service.jobs()
        table_name = "_user_summary"
        files = [str("gs:/" + f) for f in user_summary_files]
        result = jobs.insert(
            projectId=app.config["GOOGLE_CLOUD_PROJECT_ID"],
            body={
                "projectId": app.config["GOOGLE_CLOUD_PROJECT_ID"],
                "configuration": {
                    "load": {
                        "quote": "",
                        "sourceUris": files,
                        "schema": {
                            "fields": [
                                {
                                    "name": "log_date",
                                    "type": "TIMESTAMP"
                                },
                                {
                                    "name": "user_id",
                                    "type": "STRING"
                                },
                                {
                                    "name": "average_comment_karma",
                                    "type": "FLOAT"
                                },
                                {
                                    "name": "average_submission_karma",
                                    "type": "FLOAT"
                                },
                                {
                                    "name": "average_unique_words_pct",
                                    "type": "FLOAT"
                                }
                            ]
                        },
                        "destinationTable": {
                            "projectId": app.config["GOOGLE_CLOUD_PROJECT_ID"],
                            "datasetId": app.config["BIGQUERY_DATASET_ID"],
                            "tableId": table_name
                        }
                    }
                }

            }
        ).execute()
        logging.info(result)

def export_user_summary_map(user):
    """Map function for exporting User entities."""
    unique_word_count = int(user.data["summary"]["comments"]["unique_word_count"])
    total_word_count = int(user.data["summary"]["comments"]["total_word_count"])

    total_comment_karma = int(user.data["summary"]["comments"]["computed_karma"])
    total_comments = int(user.data["summary"]["comments"]["count"])

    total_submission_karma = int(user.data["summary"]["submissions"]["computed_karma"])
    total_submissions = int(user.data["summary"]["submissions"]["count"])

    row = "%s,%s,%s,%s,%s\n" % (
        user.last_updated.strftime("%Y-%m-%d %H:%M"),
        user.key.id(),
        total_comment_karma*1.00/max(total_comments,1),
        total_submission_karma*1.00/max(total_submissions,1),
        unique_word_count*100.0/max(total_word_count,1)
    )
    yield row

def export_user_summary_handler():
    """Handler function for exporting User entities."""
    today = datetime.datetime.combine(datetime.date.today(), datetime.time())
    yesterday = today - datetime.timedelta(hours=24)
    mr_pipeline = ExportUserSummaryPipeline(yesterday, today)
    mr_pipeline.start()
    path = mr_pipeline.base_path + "/status?root=" + mr_pipeline.pipeline_id
    return "Kicked off job: %s" % path


class UpdateSubscribersPipeline(pipeline.Pipeline):
    """A pipeline that updates subscriber counts for subreddits."""
    def run(self):
        """Update Subreddit subscribers counts."""
        yield mapreduce_pipeline.MapperPipeline(
            "UpdateSubscribersPipeline",
            "application.views.update_subscribers_map",
            "mapreduce.input_readers.GoogleCloudStorageInputReader",
            params={
                "input_reader": {
                    "bucket_name": app.config["GCS_BUCKET_NAME"],
                    "objects": ["subreddits/subscribers/delta/*"]
                }
            },
            shards=8
        )

def update_subscribers_map(delta):
    """Map function for updating Subreddit subscribers counts."""
    lines = delta.read().split("\n")
    for batch in chunk(lines, 100):
        id_subs = [(x.split(",")[0], x.split(",")[1]) for x in batch if "," in x]
        subs = [x for x in ndb.get_multi([ndb.Key("Subreddit", s[0]) for s in id_subs]) if x]
        for sub in subs:
            sub.subscribers = int([x[1] for x in id_subs if x[0] == sub.key.id()][0])
        ndb.put_multi(subs)

def update_subscribers_handler():
    """Handler function for updating Subreddit subscribers counts."""
    mr_pipeline = UpdateSubscribersPipeline()
    mr_pipeline.start()
    path = mr_pipeline.base_path + "/status?root=" + mr_pipeline.pipeline_id
    return "Kicked off job: %s" % path

@admin_required
def delete_user(username):
    """Deletes user given username."""
    user = User.query(User.username == username).get()
    user.key.delete()
    return "OK"

def update_trends():
    """Updates trending subreddits for each category."""
    trend_keys = ["new_subs", "trending_subs", "growing_subs"]
    categories = get_all_subreddit_categories()
    for trend_key in trend_keys:
        data = bq_query(trend_key, cached=False) or []
        for sub in data:
            parent_name = [
                x for x in categories if x["id"] == sub["parent_id"]
            ][0]["text"].split(">")[-1].strip()
            sub["parent_name"] = parent_name
        PreprocessedItem(
            id=trend_key,
            data=json.dumps(data)
        ).put()
    data = bq_query("trending_subs_in_cats", cached=False)
    trends = []
    for category in categories:
        cat_data = [x for x in data if x["parent_id"] == category["id"]]
        trends.append(
            PreprocessedItem(
                id="trending_%s" % category["id"],
                data=json.dumps(cat_data)
            )
        )
    ndb.put_multi(trends)
    return "Done"

def update_search_subscribers():
    """Updates search index entries for subreddits that have grown."""
    search_subs = bq_query("update_search_subs", cached=False)
    index = search.Index(name="subreddits_search")
    for search_chunk in chunk(search_subs, 200):
        docs = []
        for sub in search_chunk:
            doc = index.get(sub["subreddit_id"])
            if not doc:
                continue
            doc_fields = []
            subscribers = sub["current_subscribers"]
            for field in doc.fields:
                if field.name == "subscribers":
                    doc_fields.append(
                        search.NumberField(
                            name='subscribers',
                            value=subscribers or 0
                        )
                    )
                else:
                    doc_fields.append(field)
            doc = search.Document(
                doc_id=doc.doc_id,
                fields=doc_fields,
                rank=subscribers if subscribers > 0 else 1
            )
            docs.append(doc)
        index.put(docs)
    return "Done"

def update_preprocessed_subreddit_categories():
    categories = {c.key.id(): c.display_name for c in Category.query().fetch(1000)}
    category_names = []
    for category in categories:
        if category == 'reddit': continue
        keys = category.split("_")[1:]
        combined_keys = ["reddit_" + "_".join(keys[:keys.index(k)+1]) for k in keys]
        text = " > ".join([categories[k] for k in combined_keys])
        category_names.append({"id": category, "text": text})
    category_names.sort(key=lambda x:x["id"])
    all_categories = PreprocessedItem.get_by_id("all_subreddit_categories")
    all_categories.data = json.dumps(category_names)
    all_categories.put()
    return "Done"

def sitemap():
    """Renders sitemap XML."""
    subreddits_root = get_subreddits_root()
    sitemap_xml = render_template(
        "sitemap.xml",
        today=datetime.date.today().strftime("%Y-%m-%d"),
        subreddits_root=json.loads(subreddits_root.data)
    )
    response = make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"
    return response

def subreddit_metrics(subreddit_id):
    """Returns subreddit rank from BigQuery."""
    subreddit_rank = bq_query(
        "subreddit_rank",
        params=(subreddit_id),
        cache_key="rank_"+subreddit_id
    )
    return jsonify(
        metrics={
            "subreddit_rank": subreddit_rank[0]["subreddit_rank"]
        }
    )

def warmup():
    """Handles AppEngine warmup requests."""
    return ""

# From https://github.com/janscas/ndb-gae-pagination
def return_query_page(
        query_class,
        size=10,
        bookmark=None,
        is_prev=None,
        equality_filters=None,
        orders=None
    ):
    """
    Generate a paginated result on any class.

    Args:
        query_class: The ndb model class to query.
        size: The size of the results. Defaults to 10.
        bookmark: The urlsafe cursor of the previous queris.
                  First time will be None.
        is_prev: If you're requesting for a next result or the previous ones.
        equality_filters: a dictionary of {'property': value} to apply
                          equality filters only
        orders: a dictionary of {'property': '-' or ''} to order the results
                like .order(cls.property)
    Returns:
        a tuple (list of results, Previous and Next cursor bookmarks)
    """
    if bookmark:
        cursor = ndb.Cursor(urlsafe=bookmark)
    else:
        is_prev = None
        cursor = None

    query = query_class.query()
    try:
        for prop, value in equality_filters.iteritems():
            query = query.filter(getattr(query_class, prop) == value)

        q_forward = query.filter()
        q_reverse = query.filter()

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
