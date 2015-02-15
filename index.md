---
layout: page
title: Home
tagline:
---
{% include JB/setup %}


{% for post in site.posts %}

<div class="post">
	<div class="header">
		<h2><a href="{{ post.url }}">{{ post.title }}</a></h2>
		{% if post.tagline %}<small>{{post.tagline}}</small>{% endif %}
		<h4 class="no-top-margin">{{ post.date | date_to_long_string }}</h4>
	</div>
	<div class="content margin-btm-20">
		{{ post.content }}
	</div>
	<div class="comments">
		<a href="{{ post.url }}/#disqus_thread">Comments</a>
	</div>
</div>
{% endfor %}