---
layout: page
title: Snoop Snoo Blog
tagline:
---
{% include JB/setup %}


{% for post in site.posts %}

<div class="post">
	<div class="header">
		<h4><a href="{{ post.url }}">{{ post.title }}</a></h4>
		{% if post.tagline %}<small>{{post.tagline}}</small>{% endif %}
		<h5>{{ post.date | date_to_long_string }}</h5>
	</div>
	<div class="content">
		{{ post.content }}
	</div>
	<div class="comments">
		<a href="{{ post.url }}/#disqus_thread">Comments</a>
	</div>
</div>
{% endfor %}