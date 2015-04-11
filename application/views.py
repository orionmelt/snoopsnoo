"""
views.py

URL route handlers

"""

import re
import json
import random
from math import pow
from collections import Counter

import markdown
from google.appengine.api import memcache
from google.appengine.ext import ndb
from flask import (
    request, render_template, url_for, redirect, abort, Markup, jsonify
)

from decorators import login_required, admin_required
from application import app
from models import  (
    User, Feedback, ErrorLog, Subreddit, Category, CategoryTree, 
    PredefinedCategorySuggestion, ManualCategorySuggestion, 
    SubredditRelation, PreprocessedItem, SubredditRecommendationFeedback
)

sample_topics = [
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

def uniq(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]

def get_subreddit(display_name_lower):
    if not display_name_lower:
        return None
    subreddit = memcache.get("subreddit_" + display_name_lower)   
    if subreddit:
        return subreddit
    else:
        subreddit = Subreddit.query(
            Subreddit.display_name_lower == display_name_lower
        ).get()
        if subreddit:
            memcache.add("subreddit_" + display_name_lower,subreddit)
            return subreddit
    return None

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
    return render_template("index.html")

def about():
    return render_template("about.html")

def random_profile():
    r = ndb.Key("User", random.randrange(pow(2, 52) - 1))
    keys = User.query(User.key > r).fetch(1000, keys_only=True)
    if not keys:
        User.query(User.key < r).fetch(1000, keys_only=True)
    key = random.choice(keys)
    return redirect("/u/" + key.get().username)

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
    return render_template(
        "user_profile.html", 
        user=user, 
        data=json.dumps(user.data), 
        all_subreddit_categories=all_subreddit_categories
    )

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
    feedback = request.args.get("f") == "1"
    f = Feedback(
        username=username,
        data_key=data_key,
        data_value=data_value,
        feedback=feedback
    )
    f.put()
    return "OK"

def process_subreddit_recommendation_feedback():
    username = request.args.get("u")
    input_subreddits = request.args.get("i")
    recommended_subreddit = request.args.get("o")
    feedback = request.args.get("f") == "1"
    f = SubredditRecommendationFeedback(
        username=username,
        input_subreddits=input_subreddits,
        recommended_subreddit=recommended_subreddit,
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

def subreddits_home():
    root = get_subreddits_root()
    return render_template(
        "subreddits_home.html", 
        root=json.loads(root.data), 
        subreddit_count=root.subreddit_count, 
        last_updated=root.last_updated, 
        intro_items=random.sample(sample_topics, 3)
    )

def subreddits_category(level1, level2=None, level3=None):
    root = get_subreddits_root()
    if level1 == "adult":
        url = url_for(
            "subreddits_category",
            level1="adult-and-nsfw",
            level2=level2,
            level3=level3
        )
        if request.query_string:
            url += "?" + request.query_string
        return redirect(url)
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

    all_subreddit_categories = get_all_subreddit_categories()

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

    return render_template(
        "subreddits_category.html",
        subreddits=subreddits, 
        category=category, 
        cat_tree=category_tree, 
        breadcrumbs=breadcrumbs, 
        prev=prev_bookmark, 
        next=next_bookmark,
        all_subreddit_categories=all_subreddit_categories,
        subreddit_count=ct_object.subreddit_count,
        root=json.loads(root.data)
    )

def get_related_subreddits(subreddit_id, limit=5):
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

def subreddit(subreddit_name):
    root = get_subreddits_root()
    subreddit_name = subreddit_name.lower()
    s = get_subreddit(subreddit_name)
    if not s:
        return render_template(
            "subreddit_not_found.html", 
            subreddit=subreddit_name
        ), 404

    breadcrumbs = []
    for i,c in enumerate(s.parent_id.split("_")):
        breadcrumbs.append(
            Category.get_by_id("_".join(s.parent_id.split("_")[:i+1]))
        )

    related_subreddits = get_related_subreddits(s.key.id())
    
    all_subreddit_categories = get_all_subreddit_categories()
    
    return render_template(
        "subreddit.html", 
        subreddit=s, 
        breadcrumbs=breadcrumbs[1:], 
        all_subreddit_categories=all_subreddit_categories, 
        related_subreddits=related_subreddits,
        root=json.loads(root.data)
    )

def subreddit_frontpage():
    over18 = int(request.args.get("over18"))
    age_confirmed = int(request.args.get("age_confirmed"))
    data = request.get_json()
    return render_template(
        "subreddit_frontpage.html", 
        front_page=data, 
        over18=over18, 
        age_confirmed=age_confirmed
    )

def suggest_subreddit_category():

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
            c = PredefinedCategorySuggestion(
                subreddit_display_name=subreddit_name,
                category_id=category_id
            )
            predefined_suggestions.append(c)
        else:
            c = ManualCategorySuggestion(
                subreddit_display_name=subreddit_name,
                category_id=category_id,
                suggested_category=suggested_category
            )
            manual_suggestions.append(c)
    if predefined_suggestions:
        ndb.put_multi(predefined_suggestions)
    if manual_suggestions:
        ndb.put_multi(manual_suggestions)
    return "OK"

def find_subreddit():
    input_subreddit = request.form.get("subreddit").lower()
    if not input_subreddit:
        return redirect(url_for("subreddits_home"))
    subreddit = get_subreddit(input_subreddit)
    if subreddit:
        return redirect("/r/" + subreddit.display_name)
    else:
        return render_template(
            "subreddit_not_found.html", 
            subreddit=input_subreddit
        ), 404

def recommended_subreddits(subreddits):
    input_subreddits = [
        x.lower() \
            for x in subreddits.split(",") \
                if re.match("^[\w]+$", x) is not None
    ]
    if not input_subreddits:
        return jsonify(recommended=[])
    recommended_subreddits = []
    s_keys = Subreddit.query(
        Subreddit.display_name_lower.IN(input_subreddits)
    ).fetch(keys_only=True)
    
    for s_key in s_keys:
        r = [
            item for item in [
                x.display_name \
                    for x in get_related_subreddits(s_key.id(), limit=5)
            ] if item.lower() not in input_subreddits
        ]
        recommended_subreddits.append(r)
    if recommended_subreddits:
        f = [item for sublist in recommended_subreddits for item in sublist]
        c = Counter(f)
        l = sorted(c, key=lambda x: (-c[x], f.index(x)))
        return jsonify(recommended=l)
    else:
        return jsonify(recommended=[])

@admin_required
def delete_user(username):
    user = User.query(User.username == username).get()
    user.key.delete()
    return "OK"

def warmup():
    return ""

# From https://github.com/janscas/ndb-gae-pagination
def return_query_page(query_class, size=10, bookmark=None, is_prev=None, equality_filters=None, orders=None):
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
