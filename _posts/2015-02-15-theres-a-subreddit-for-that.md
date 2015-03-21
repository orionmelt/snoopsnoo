---
layout: post
title: "There's a subreddit for that!"
description: ""
category: 
tags: []
---
{% include JB/setup %}

There are over [9,000 active subreddits](https://www.reddit.com/about/) on reddit, and according to [reddit metrics](http://redditmetrics.com/history), over 585,000 in total! There's probably a subreddit for any topic you can think of, no matter how obscure or specific. (If not, you can create one yourself.) So there's indeed a subreddit for that, for pretty much any value of that. That's great, but how do you actually find new subreddits?

I think there are two interesting areas where there's a lot of room for improvement &mdash; subreddit discovery and recommendations.

###Subreddit Discovery

There are already a few resources to help you find subreddits:

1. reddit's own [subreddit listing page](http://www.reddit.com/subreddits).
2. Meta subreddits such as [/r/SubredditOfTheDay](http://www.reddit.com/r/subredditoftheday) and [/r/FindAReddit](http://www.reddit.com/r/findareddit).
3. Third-party websites such as [reddit metrics](http://redditmetrics.com) and [redditlist](http://redditlist.com/).

These are great if you already have a specific keyword in mind, or if you are simply interested in finding new and trending subreddits regardless of topic. But what if you wanted to browse subreddits by topic, like a dmoz-style directory? You could visit [subreddits.org](http://subreddits.org/) or [metareddit.com](http://metareddit.com/tags/), but they seem outdated. So I built a [directory of subreddits](http://snoopsnoo.com/subreddits/).

**A brief background:** while building <span class="logo logo-small">SNOOP<img src="{{ ASSET_PATH }}snoopsnoo/img/logo_sm.png" alt="(SnoopSnoo Logo)" width="21" height="10">SNOO</span>, I decided to manually group the top 2,500 subreddits by topics so I would be able to tell, at least at a high level, what subject areas a user was interested in. For example, it was straightforward to presume that a user's activity in /r/python and /r/java meant that they were interested in "Technology > Programming". The tedious (_and painful_) prerequisite was, of course, having to manually file /r/python and /r/java under "Programming" (and do this for each of the 2,500 subreddits). After several frustrating attempts, I managed to categorize most of the top 2,500 subreddits under several topics and continued to build the rest of the site. I then realized that I had already created a mini-directory subreddits grouped by topic!

The next logical step was to expand the directory by adding more subreddits, but doing it manually wasn't going to scale. So, like any <strike>lazy</strike> good programmer, I automated the process:

* For each of the top ~13,000 subreddits, I gathered a list of its related subreddits. I used sidebar links and crossposts to measure relativity between subreddits. This gave me a list of around 28,000 subreddits.
* I filtered out subreddits with fewer than 1,000 subscribers to keep things simple, which shortened the list down to around 19,000 subreddits.  
* <span class="logo logo-small">SNOOP<img src="{{ ASSET_PATH }}snoopsnoo/img/logo_sm.png" alt="(SnoopSnoo Logo)" width="21" height="10">SNOO</span> currently lets users suggest topics for subreddits that have none assigned. Using this helpful data along with the manual list I already had, I wrote a program to automatically assign topics to the remaining subreddits.
* Subreddits that couldn't be assigned a topic (such as self-post only subreddits that have no useful crossposts data) were assigned "General" by default. 

And that's how I built a directory of thousands of subreddits categorized by topic. You can [check it out here](http://snoopsnoo.com/subreddits/) and I hope you find it useful.

###Subreddit Recommendations

Another problem that I find interesting is recommending subreddits based on user activity. Currently, reddit doesn't seem to provide tailored subreddit recommendations to users based on their activity. For instance, if you are already active on /r/Cooking and /r/recipes, perhaps you would also like /r/AskCulinary or /r/budgetfood? 

Since I now have enough data about subreddits , I figured it'd be worth adding subreddit recommendations to <span class="logo logo-small">SNOOP<img src="{{ ASSET_PATH }}snoopsnoo/img/logo_sm.png" alt="(SnoopSnoo Logo)" width="21" height="10">SNOO</span> &mdash; it now shows recommendations for subreddits that you may like and also lets you vote on how useful you find them. As always, user feedback is extremely helpful in improving my algorithms and I look forward to all kinds of feedback, suggestions and criticism.

**Making it better:** *While this recommendation technique (known as content-based filtering) is better than completely random choices, it is still very limited by nature. If I deduce that you are interested in cooking, I can only recommend subreddits related to cooking and food at best. A more useful recommendation system would also do what is known as collaborative filtering, where recommendations are derived using not only the type of content a user already likes, but also from new content liked by similar users. This is a harder problem to solve and requires a lot more data than I currently have, but it's something that I hope to explore in the near future.*



