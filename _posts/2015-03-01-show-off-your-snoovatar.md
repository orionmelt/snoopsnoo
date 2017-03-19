---
layout: post
title: "Show off your snoovatar"
description: ""
category: 
tags: []
---
{% include JB/setup %}

In the latest edition of "Features Nobody Requested", I am happy to announce that <span class="logo logo-small">SNOOP<img src="{{ ASSET_PATH }}snoopsnoo/img/logo_sm.png" alt="(SnoopSnoo Logo)" width="21" height="10">SNOO</span> now displays your snoovatar (if you have gold and have set one up)! It looks like this:

![SnoopSnoo now shows snoovatars!](https://i.imgur.com/OL5bvL1.png)

As far as I know, [reddit doesn't give you access to snoovatars via the API](https://www.reddit.com/r/blog/comments/2rnf1z/create_your_own_reddit_alien_avatar_with_reddit/cnhgy57) and it's not a matter of simply scraping a static image from your snoovatar page either, because it's dynamically constructed using JavaScript and Canvas. So I wrote some simple code to generate it myself using the [Python Imaging Library](https://en.wikipedia.org/wiki/Python_Imaging_Library). If you come across any issues, please let me know.

The code is available as a [Blockspring function](https://api.blockspring.com/orionmelt/99cd0d8656e4608468d6b1c7e18ce4de) if you're interested &mdash; just enter your username and run the function to generate your snoovatar in PNG format. To use it in your own app, sign up for Blockspring and use your API key to call the function &mdash; they make it ridiculously simple to integrate APIs like these in your apps, [check them out](https://www.blockspring.com/)!