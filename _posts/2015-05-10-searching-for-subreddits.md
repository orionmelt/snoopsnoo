---
layout: post
title: "Searching for subreddits"
description: ""
category: 
tags: []
---
{% include JB/setup %}

reddit announced last week that they're bringing back the reddit.com beta testing program, and one of the interesting new features is the [improved subreddit search](http://www.reddit.com/r/beta/comments/35762a/welcome_to_rbeta/). As the admins themselves admit, searching for subreddits has always been a major pain point, and the new search vastly improves the quality of results. I had been working on a subreddit search feature for <span class="logo logo-small">SNOOP<img src="{{ ASSET_PATH }}snoopsnoo/img/logo_sm.png" alt="(SnoopSnoo Logo)" width="21" height="10">SNOO</span> as well, and right now seems like a good time to release it!

Let's compare reddit's old and new search algorithms &mdash; searching for ["robots" using the old search](https://www.reddit.com/subreddits/search?q=robots&sort=activity) gives us results with /r/DaftPunk and /r/plotholes pretty high up in the list, presumably because both these subreddits include the word "robots" in their descriptions. The [new search for "robots"](https://beta.reddit.com/subreddits/search?q=robots) returns results that are a lot more relevant &mdash; /r/DaftPunk and /r/plotholes still appear, but they are preceded by subreddits that are actually about robots. Great!

Now, how can <span class="logo logo-small">SNOOP<img src="{{ ASSET_PATH }}snoopsnoo/img/logo_sm.png" alt="(SnoopSnoo Logo)" width="21" height="10">SNOO</span> improve search results? One advantage it has is that it *knows* /r/DaftPunk is about music and /r/plotholes is about movies, thanks to the categorization of subreddits that I had [written about earlier](http://blog.snoopsnoo.com/2015/02/15/theres-a-subreddit-for-that). And this comes in handy when searching for subreddits. 

Let's [search for "robots"](http://snoopsnoo.com/subreddits/search?q=robots) on <span class="logo logo-small">SNOOP<img src="{{ ASSET_PATH }}snoopsnoo/img/logo_sm.png" alt="(SnoopSnoo Logo)" width="21" height="10">SNOO</span>. Thanks to [stemming](http://en.wikipedia.org/wiki/Stemming), it also includes results for "robotics". Yay! Of course, not-entirely-relevant subreddits such as /r/DaftPunk, /r/plotholes and /r/robotchicken are included (and they should be, because they do have the word "robots" in them somwehere), but the search lets you restrict your results to particular topics &mdash; [search for "robots topic:technology"](http://snoopsnoo.com/subreddits/search?q=robots+topic%3Atechnology), and only subreddits that are classified under Technology are returned. 

Let's look at a few more interesting examples:

* [Searching for "python"](http://snoopsnoo.com/subreddits/search?q=python) returns /r/pygame &mdash; even though the word "python" does not appear in the subreddit's title or description, because we know that it is classified under the Python topic. The search results also include /r/montypython and /r/ballpython, but [add "topic:programming" to your search query](http://snoopsnoo.com/subreddits/search?q=python+topic%3Aprogramming) and they're gone. On the other hand, if you're really looking for subreddits about the *other* python, simply [search for "python topic:animals"](http://snoopsnoo.com/subreddits/search?q=python+topic%3Aanimals).
* [Searching for "universities in texas"](http://snoopsnoo.com/subreddits/search?q=universities+in+texas) returns /r/aggies, because we know that the subreddit is about "Universities and Colleges" and because "Texas" appears in its title/description.
* [Searching for "india"](http://snoopsnoo.com/subreddits/search?q=india) returns /r/mumbai and /r/bangalore (although only on page 2), even when they don't have the word India in their title or description.

The search also supports a small number of filters that I hope you find useful:

* ["cats subscribers<5000"](http://snoopsnoo.com/subreddits/search?q=cats+subscribers%3C5000) returns subreddits about cats that have fewer than 5000 subscribers, for when you are purposely looking for smaller subreddits.
* ["music created>2013-05-10"](http://snoopsnoo.com/subreddits/search?q=music+created%3E2013-05-10) returns subreddits about music that were created within the past two years.
* ["hardcore over18:false"](http://snoopsnoo.com/subreddits/search?q=hardcore+over18%3Afalse) excludes 18+ subreddits from the results. Use "over18:true" if you only want 18+ subreddits returned &mdash; the search does not judge.

It's exciting to release this new feature, but it does have its limitations &mdash; it only searches subreddit metadata, not content in posts. The index is also currently limited to the 30K subreddits that I have data for, but I'm working hard on adding more and more subreddits.

Thanks for reading, and I hope you enjoy the new search feature. Feedback and bug reports are welcome!
