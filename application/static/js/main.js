var g_base_results = "";
var g_username = "";
var g_last_updated = "";
var debug = false;
var g_user_data = {
    "about": null,
    "comments": [],
    "submissions": [],
};

var g_user_timezone = jstz.determine().name();

var FULL_WIDTH=860;
var HALF_WIDTH=430;

var SYNOPSIS_KEYS = [
    {label: "you are", key:"gender"},
    {label: "you are", key:"orientation"},
    {label: "you are in a relationship with your", key:"relationship_partner"}, 
    {label: "you live(d)", key:"places_lived"}, 
    {label: "you grew up", key:"places_grew_up"},
    {label: "people in your family", key:"family_members"}, 
    {label: "you have these pets", key:"pets"}, 
    {label: "things you've said you like", key:"favorites"}, 
    {label: "you are", key:"attributes"},
    {label: "you have", key:"possessions"}, 
    {label: "your locations of interest", key:"locations"}, // For backward compatibility with v1 data
    {label: "your locations of interest", key:"location"}, 
    {label: "you like to watch", key:"tv_shows"}, 
    {label: "you like", key:"interests"}, 
    {label: "you like playing", key:"games"}, // For backward compatibility with v1 data
    {label: "you like playing", key:"gaming"}, 
    {label: "sports and teams you like:", key:"sports"}, 
    {label: "you like listening to", key:"music"}, 
    //{label: "you use", key:"drugs"}, 
    {label: "you like to read", key:"books"},
    {label: "you like", key:"celebs"}, // For backward compatibility with v1 data
    {label: "you like", key:"celebrities"},
    {label: "you are interested in", key:"business"}, 
    {label: "you like", key:"entertainment"},
    {label: "you are interested in", key:"science"}, 
    {label: "you are interested in", key:"tech"}, // For backward compatibility with v1 data
    {label: "you are interested in", key:"technology"},
    {label: "you are interested in", key:"lifestyle"}, 
    {label: "you like to discuss", key:"others"}, // For backward compatibility with v1 data
    {label: "you like to discuss", key:"other"}, 
    {label: "you like to discuss", key:"news & politics"}, 
    {label: "you have", key:"gadget"}, 
    {label: "you are", key:"political_view"}, 
    {label: "you are", key:"physical_characteristics"}, 
    {label: "your religious beliefs", key:"religion"}
];

var CATEGORIES = [
    'Anthropology',
    'Archaeology',
    'Architecture',
    'Art',
    'Business',
    'Entertainment',
    'Gaming',
    'History',
    'Interests',
    'Law',
    'Lifestyle',
    'Location',
    'Meta',
    'Music',
    'News & Politics',
    'Organization',
    'Philosophy',
    'Psychology',
    'Science',
    'Sports',
    'Technology',
    'Travel',
    'General'
];

var SUB_CATEGORIES = [
    'Anime',
    'Astronomy',
    'Automobiles',
    'Backpacking',
    'Baseball',
    'Basketball',
    'Biology',
    'Board/Card Games',
    'Books',
    'Botany',
    'Camping',
    'Celebrities',
    'Chemistry',
    'Chess',
    'City',
    'Classical',
    'Climbing',
    'Comedy',
    'Comics',
    'Computer Science',
    'Cooking',
    'Country',
    'Crafts',
    'Cycling',
    'Data Visualization',
    'Design',
    'Discussion',
    'DIY',
    'Drugs',
    'Dubstep',
    'Economics',
    'Electronic',
    'Employment',
    'Engineering',
    'Entrepreneurship',
    'Fantasy',
    'Fashion',
    'Finance',
    'Fitness',
    'Food',
    'Football',
    'Gadgets',
    'Gardening',
    'General Business',
    'General Science',
    'General Technology',
    'Geology',
    'Golf',
    'Graffiti',
    'Hardware',
    'Health',
    'Hiking',
    'Hip Hop',
    'Hockey',
    'Horror',
    'House',
    'Humor',
    'Internet',
    'Jazz',
    'Longboarding',
    'Marketing',
    'Math',
    'Medicine',
    'Memes',
    'Metal',
    'MMA',
    'Mobile',
    'Motivation',
    'Motorsports',
    'Movies',
    'Music',
    'Networking',
    'Other',
    'Personal Finance',
    'Photography',
    'Physics',
    'Pictures',
    'Politics',
    'Pop',
    'Programming',
    'Punk',
    'Rap',
    'Relationships',
    'Religion',
    'Rock',
    'Rugby',
    'Science Fiction',
    'Shopping',
    'Skateboarding',
    'Skiing',
    'Skydiving',
    'Snowboarding',
    'Soccer',
    'Software',
    'State',
    'Tennis',
    'Trance',
    'TV Shows',
    'University',
    'USMC',
    'Video Games',
    'Videos',
    'World News',
    'Wrestling',
    'Writing'
]

var ERROR_MSGS = {
    "UNEXPECTED_ERROR": "An unexpected error has occurred. Please try again in a few minutes.",
    "USER_NOT_FOUND": "User not found.",
    "NO_DATA": "No data available.",
    "REQUEST_CANCELED": "Server too busy. Please try again in a few minutes.",
    "SERVER_BUSY": "Server too busy. Please try again in a few minutes."
}

$(function () {
    $(".user-timezone").text(g_user_timezone);
    $("[data-hide]").on("click", function(){
        $(this).closest("#error").hide();
    });
});

function jqXHR_error(jqXHR, status_text, error_thrown, error_message) {
    if(jqXHR.status===404) {
        $("#error-message").text(ERROR_MSGS["USER_NOT_FOUND"]);
        var error_object = {"username":g_username, "error_type": "USER_NOT_FOUND", "error_message":error_message};
    } else if(jqXHR.status===0 && !jqXHR.responseText) {
        $("#error-message").text(ERROR_MSGS["REQUEST_CANCELED"]);
        var error_object = {"username":g_username, "error_type": "REQUEST_CANCELED", "error_message":error_message};
    } else {
        $("#error-message").text(ERROR_MSGS["UNEXPECTED_ERROR"]);
        var error_object = {"username":g_username, "error_type": "UNEXPECTED_ERROR", "error_message":error_message};
    }
    $("#error").show();
    log_error(error_object);
    $("#go").button("reset");
}

function app_error(error_type, error_message) {
    $( "#error-message" ).text(ERROR_MSGS[error_type]); 
    $( "#error" ).show();
    var error_object = {"username":g_username, "error_type": error_type, "error_message":error_message};
    log_error(error_object);
    $("#go").button("reset");
}

function get_data(username) {
    g_username=username;
    get_about(username);
}

function get_about(username) {
    var about_url = "http://www.reddit.com/user/" + username + "/about.json";
    $.ajax({
        url: about_url,
        timeout: 30000,
    }).done(function(data) {
        g_user_data["about"] = data.data;
        setTimeout(function() {
            get_comments(username);
        }, 2000);
    }).fail(function(jqXHR, status_text, error_thrown) {
        jqXHR_error(jqXHR, status_text, error_thrown, "Error getting about.json");
    });
}

function get_comments(username) {
    var more = true;
    var after = null;
    var base_url = "http://www.reddit.com/user/" + username + "/comments/.json?limit=100";
    var url = base_url;
    get_comment_page(base_url,after);
}

function get_comment_page(url,after,count) {
    //if(after) url+="&after="+after;
    $.ajax({
        url: after?url+"&after="+after:url,
        timeout: 30000,
    }).done(function(data) {
        if(!count) {
            count=100; 
        } else {
            count+=100;
        }
        $("#go").html("Fetching " + count + " comments <i class='fa fa-spinner fa-spin'></i>");
        if(data.data && data.data.children) {
            data.data.children.forEach(function(d) {
                g_user_data["comments"].push({
                    "id": d.data.id,
                    "subreddit": d.data.subreddit,
                    "text": d.data.body,
                    "created_utc": d.data.created_utc,
                    "score": +d.data.score,
                    "submission_id": d.data.link_id.substring(3),
                    "edited": d.data.edited,
                    "top_level": d.data.parent_id.lastIndexOf("t3")===0,
                    "gilded": d.data.gilded,
                    "permalink": "http://www.reddit.com/r/" + d.data.subreddit + "/comments/" + d.data.link_id.substring(3) + "/_/" + d.data.id
                });
            });
            if(data.data.after) {
                after = data.data.after;
                //url = url + "&after=" + after;
                setTimeout(function() {
                    get_comment_page(url,after, count);
                }, 2000);
            } else {
                get_submissions(g_username);
            }
        } else {
            // ERROR
        }
    }).fail(function(jqXHR, status_text, error_thrown) {
        console.log(jqXHR);
        jqXHR_error(jqXHR, status_text, error_thrown, "Error getting comments.json");
    });
}

function get_submissions(username) {
    var more = true;
    var after = null;
    var base_url = "http://www.reddit.com/user/" + username + "/submitted/.json?limit=100";
    var url = base_url;
    setTimeout(function() {
        get_submission_page(base_url,after);
    }, 2000);
}

function get_submission_page(url,after,count) {
    //if(after) url+="&after="+after;
    $.ajax({
        url: after?url+"&after="+after:url,
        timeout: 30000,
    }).done(function(data) {
        if(!count) {
            count=100; 
        } else {
            count+=100;
        }
        $("#go").html("Fetching " + count + " submissions <i class='fa fa-spinner fa-spin'></i>");
        if(data.data && data.data.children) {
            data.data.children.forEach(function(d) {
                g_user_data["submissions"].push({
                    "id": d.data.id,
                    "subreddit": d.data.subreddit,
                    "text": d.data.selftext,
                    "created_utc": d.data.created_utc,
                    "score": +d.data.score,
                    "permalink": "http://www.reddit.com" + d.data.permalink,
                    "url": d.data.url,
                    "title": d.data.title,
                    "is_self": d.data.is_self,
                    "gilded": d.data.gilded,
                    "domain": d.data.domain
                });
            });
            if(data.data.after) {
                after = data.data.after;
                //url = url + "&after=" + after;
                setTimeout(function() {
                    get_submission_page(url,after,count);
                }, 2000);
            } else {
                call_blockspring();
            }
        } else {
            // ERROR
        }
    }).fail(function(jqXHR, status_text, error_thrown) {
        jqXHR_error(jqXHR, status_text, error_thrown, "Error getting submitted.json");
    });
}

function call_blockspring() {
    $("#go").html("Processing <i class='fa fa-spinner fa-spin'></i>");
    if(!(g_user_data.comments.length || g_user_data.submissions.length)) {
        app_error("NO_DATA", ERROR_MSGS["NO_DATA"])
        return;
    }
    $.ajax({
            url: "https://sender.blockspring.com/api_v1/blocks/15d8e54759752564d45241992687b98f?api_key=d1b2e14d5b005465cfe3c83976a9240a",
            type: "POST",
            data: { username: g_username, json_data: JSON.stringify(g_user_data)},
            crossDomain: true
    }).done(function(response){
        //Data is here from API
        if(response.error) {
            app_error("UNEXPECTED_ERROR",response.error);
        } else if(!response.results) {
            app_error("SERVER_BUSY","");
        } else {
            var blockspring_results = JSON.parse(response.results);
            if(blockspring_results) {
                var sherlock_results = JSON.parse(blockspring_results.result);
                if(sherlock_results) {
                    g_username = sherlock_results.username;
                    //Update data in local DB
                    $.ajax({
                        url: "/update",
                        type: "POST",
                        contentType: "application/json",
                        data: JSON.stringify(sherlock_results),
                    }).done(function(response) {
                        if(response=="OK") {
                            //Now user exists in local DB, forward to profile page
                            window.location.href = "/u/"+g_username;
                        } else if(response=="NO_DATA") {
                            app_error("NO_DATA", "");
                        }
                    });
                } else {
                    app_error("SERVER_BUSY","");
                }
            } else {
                app_error("SERVER_BUSY","");
            }
        }
        /*
        results = JSON.parse(response.results);
        result = JSON.parse(results.result);
        if(!response.error && result) {
            g_username = result.username;
            //Update data in local DB
            $.ajax({
                url: "/update",
                type: "POST",
                contentType: "application/json",
                data: JSON.stringify(results),
            }).done(function(response) {
                if(response=="OK") {
                    //Now user exists in local DB, forward to profile page
                    window.location.href = "/u/"+g_username;
                } else if(response=="NO_DATA") {
                    $( "#error-message" ).text("No data available.");
                    $( "#error" ).show();
                    var error_object = {"username":g_username, "error_type": "empty", "error_message":null};
                    log_error(error_object);
                }
            });
        } else if(response.error) {
            console.log(response.error);
            app_error("UNEXPECTED_ERROR",response.error);

        } else {
            app_error("SERVER_BUSY","");
        }
        */
        
    }).fail(function(jqXHR, status_text, error_thrown) {
        jqXHR_error(jqXHR, status_text, error_thrown, "Error while calling Blockspring");
    });
}

function convert_to_v2(data) {
    var computed_comment_karma = 0,
        computed_submission_karma = 0,
        average_comment_karma = 0,
        average_submission_karma = 0;

    computed_comment_karma = data.stats.metrics.date.map(function(d) {
        return d.comment_karma;
    }).reduce(function(p,c) {
        return p+c;
    }, 0);

    computed_submission_karma = data.stats.metrics.date.map(function(d) {
        return d.submission_karma;
    }).reduce(function(p,c) {
        return p+c;
    }, 0);

    average_comment_karma = +(computed_comment_karma/data.stats.basic.comments.count).toFixed(2);
    average_submission_karma = +(computed_submission_karma/data.stats.basic.submissions.count).toFixed(2);

    var v2 = {
        "version": 2,
        "username": data.username,
        "summary": {
            "signup_date": {
                "date": Date.parse(data.stats.basic.signup_date)/1000,
                "humanized": data.stats.basic.signup_date_text,
            },
            "first_post_date": {
                "date": Date.parse(data.stats.basic.first_post_date)/1000,
                "humanized": data.stats.basic.first_post_date_text
            },
            "lurk_period": {
                "from": Date.parse(data.stats.basic.lurk_streak.date1)/1000,
                "to": Date.parse(data.stats.basic.lurk_streak.date2)/1000,
                "days_humanized": data.stats.basic.lurk_streak.duration
            },
            "comments": {
                "count": data.stats.basic.comments.count,
                "gilded": data.stats.basic.comments.gilded,
                "all_time_karma": data.stats.basic.comment_karma,
                "computed_karma": computed_comment_karma,
                "average_karma": average_comment_karma,
                "best": data.stats.basic.comments.best,
                "worst": data.stats.basic.comments.worst,
                "total_word_count": data.stats.basic.words_in_posts.total_word_count, //Fix to exclude words in submissions
                "unique_word_count": data.stats.basic.words_in_posts.unique_word_count, //Fix to exclude words in submissions
                "karma_per_word": data.stats.basic.words_in_posts.karma_per_word, //Fix to exclude words in submissions
                "hours_typed": data.stats.basic.words_in_posts.hours_typed
            },
            "submissions": {
                "count": data.stats.basic.submissions.count,
                "gilded": data.stats.basic.submissions.gilded,
                "all_time_karma": data.stats.basic.link_karma,
                "computed_karma": computed_submission_karma,
                "average_karma": average_submission_karma,
                "best": data.stats.basic.submissions.best,
                "worst": data.stats.basic.submissions.worst,
                "type_domain_breakdown": data.stats.metrics.submissions 
            }
        },
        "synopsis": {},
        "metrics": {
            "date": data.stats.metrics.date,
            "hour": data.stats.metrics.hour,
            "weekday": data.stats.metrics.weekday,
            "subreddit": data.stats.metrics.subreddit,
            "topic": data.stats.metrics.topic,
            "common_words": data.stats.common_words
        }
    }
    for(var key in data.about) {
        if(data.about.hasOwnProperty(key)) {
            if(key==="derived_attributes") continue;
            var s = {};
            var d_key = ["drugs", "locations", "possessions"].indexOf(key)!=-1 ? key.substring(0, key.length-1) : key;

            if(data.about[key]) {
                if(typeof data.about[key] === "string") {
                    s["data"] = [{
                        "value": data.about[key],
                        "count": null,
                        "sources": null
                    }];
                } else if($.isArray(data.about[key])) {
                    if(data.about[key].length) s["data"] = data.about[key];
                } else if(typeof data.about[key] === "object" && data.about[key].core && data.about[key].core.length) {
                    s["data"] = data.about[key].core;
                } else if(typeof data.about[key] === "object" && data.about[key].more && data.about[key].more.length) {
                    s["data_extra"] = data.about[key].more;
                } else if(typeof data.about[key] === "object") {

                } else {
                    //What could this be?
                }
            }
            if(data.about["derived_attributes"] && data.about["derived_attributes"][d_key]) {
                if(typeof data.about["derived_attributes"][d_key] === "string") {
                    s["data_derived"] = {
                        "value": data.about["derived_attributes"][d_key],
                        "count": null,
                        "sources": null
                    }
                } else if($.isArray(data.about["derived_attributes"][d_key])) {
                    if(data.about["derived_attributes"][d_key].length) {
                        s["data_derived"] = [];
                        data.about["derived_attributes"][d_key].forEach(function(d) {
                             s["data_derived"].push({
                                "value": d[0],
                                "count": d[1],
                                "sources": null
                            });
                        });
                        
                    }
                } else {
                    //What could this be?
                }
            }

            if(s.data || s.data_derived) {
                v2.synopsis[key] = s;
            }
        }
    }
    for(var key in data.about.derived_attributes) {
        var o_key = ["drug", "location", "possession"].indexOf(key)!=-1 ? key+"s" : key;
        if(data.about.hasOwnProperty(o_key)) continue;
        if(data.about.derived_attributes.hasOwnProperty(key)) {
            var s = {};
            if(data.about.derived_attributes[key]) {
                if(data.about.derived_attributes[key].length) {
                    s["data_derived"] = [];
                    data.about["derived_attributes"][key].forEach(function(d) {
                         s["data_derived"].push({
                            "value": d[0],
                            "count": d[1],
                            "sources": null
                        });
                    });
                }
            }
            if(s.data_derived) v2.synopsis[key]=s;
        }
    }

    // Fix Lifestyle/Drugs issue
    if(v2.synopsis.drugs && v2.synopsis.lifestyle) {
        v2.synopsis.lifestyle.data = v2.synopsis.lifestyle.data.filter(function(d) {
            if(!v2.synopsis.drugs.data.indexOf(d.value)) return d;
        });
    }
    return v2;
}

function flatten_subreddits_tree(tree, flattened_array) {
    var a = flattened_array;
    if(!a) {
        a = [];
    }
    if(tree.hasOwnProperty("children")) {
        tree["children"].forEach(function(c) {
            flatten_subreddits_tree(c,a);
        })
    } else {
        a.push({
            "name": tree["name"], 
            "submissions": tree["submissions"],
            "comments": tree["comments"],
            "submission_karma": tree["submission_karma"],
            "comment_karma": tree["comment_karma"],
            "posts": tree["posts"],
            "karma": tree["karma"],
            "average_karma_per_comment": +tree["comments"]>0 ? +(+tree["comment_karma"]/+tree["comments"]).toFixed(2) : null,
            "average_karma_per_submission": +tree["submissions"]>0 ? +(+tree["submission_karma"]/+tree["submissions"]).toFixed(2) : null,
        });
    }
    return a;
}

function send_feedback(key, value, feedback) {
    url = "/feedback?u="+g_username+"&k="+key+"&v="+value+"&f="+feedback;
    $.ajax({
        url: url,
        type: "GET"
    });
}

function log_error(error_object) {
    url = "/error-log?u="+error_object.username+"&t="+error_object.error_type+"&m="+error_object.error_message;
    $.ajax({
        url: url,
        type: "GET"
    });
}

function wrap_data(key, text, sources, confidence) {
    var source_links = "";
    sources && sources.forEach(function (s) {
        source_links += " <a href=\""+s+"\" target=\"_blank\">#</i></a> ";
    });
    var c = "content";
    if(!confidence) c = "likely";
    return  '<span class="data-block">' + 
                '<span class="' + c + '">' + text + 
                '</span>' + 
                '<span class="feedback">' +
                    '<a class="correct" data-key="' + key + '" data-value="' + text + '"" data-feedback="1" href="#">' + 
                        '<i class="fa fa-check-circle-o"  data-toggle="tooltip" data-placement="top" title="" data-original-title="This is correct"></i>' + 
                    '</a> ' + 
                    '<a class="incorrect" data-key="' + key + '" data-value="' + text + '" data-feedback="0" href="#">' +
                        '<i class="fa fa-times-circle-o" data-toggle="tooltip" data-placement="top" title="" data-original-title="This is incorrect/gibberish"></i>' +
                    '</a> ' + 
                '</span>' + 
                '<span class="feedback">' +
                source_links + 
                '</span>' + 
            '</span>';
}

function word_cloud(words_array) {
    var data = JSON.parse(JSON.stringify(words_array));
    var fill = d3.scale.category20();
    if(!data.length) return;
    min_count = data[data.length-1].size-1;
    max_count = data[0].size;

    d3.layout.cloud().size([430, 430])
        .words(data)
        .padding(5)
        .rotate(function() { return ~~(Math.random() * 2) * 90; })
        .fontSize(function(d,i) {
            size = (60*(d.size-min_count))/(max_count-min_count);
            return size>12 ? size : 12;
        })
        .on("end", draw)
        .start();

    function draw(words) {
        d3.select("#data-common_words").append("svg")
            .attr("width", 430+40+40)
            .attr("height", 430)
            .append("g")
            .attr("transform", "translate(255,215)")
            .selectAll("text")
            .data(words)
        .enter().append("text")
            .style("font-size", function(d) { return d.size + "px"; })
            .style("fill", function(d, i) { return fill(i); })
            .attr("text-anchor", "middle")
            .attr("transform", function(d) {
                return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
            })
            .text(function(d) { return d.text; });
    }
}

function populate_results(results) {
    $("#user-results").empty();
    $("#user-results").html(g_base_results);
    var _data = JSON.parse(results);
    var data;
    if(_data.version) { // Check if version in [2,3]?
        data = _data;
    } else {
        data = convert_to_v2(_data);
    }
    g_username = data.username;
    if(location.search.substring(1)==="debug") debug=true;
    if(debug) {
        console.log(JSON.parse(results));
        console.log(data);
    }

    var offset_hours = Math.floor(new Date().getTimezoneOffset()/60);

    // Summary
    $("#data-signup_date").text(new Date(data.summary.signup_date.date*1000).toLocaleDateString());
    $("#data-signup_date_humanized").text(data.summary.signup_date.humanized);

    $("#data-first_post_date").text(new Date(data.summary.first_post_date.date*1000).toLocaleDateString());
    $("#data-first_post_date_humanized").text(data.summary.first_post_date.humanized);

    $("#data-lurk_period_humanized").text(data.summary.lurk_period.days_humanized);
    $("#data-lurk_period_dates").text(new Date(data.summary.lurk_period.from*1000).toLocaleDateString() + " to " + new Date(data.summary.lurk_period.to*1000).toLocaleDateString());

    if(data.summary.submissions.gilded>0) {
        $("#data-submissions_gilded").html("<a href='http://www.reddit.com/user/" + data.username + "/gilded' target='_blank'>" 
            + data.summary.submissions.gilded + " times from submissions</a>");
    } else {
        $("#data-submissions_gilded").text(data.summary.submissions.gilded + " submissions");
    }

    if(data.summary.comments.gilded>0) {
        $("#data-comments_gilded").html("<a href='http://www.reddit.com/user/" + data.username + 
            "/gilded' target='_blank'>" + data.summary.comments.gilded + " times from comments</a>");
    } else {
        $("#data-comments_gilded").text(data.summary.comments.gilded + " comments");
    }

    $("#data-submission_karma").text(data.summary.submissions.computed_karma);
    $("#data-total_submissions").text(data.summary.submissions.count);
    $("#data-reddit_submission_karma").text(data.summary.submissions.all_time_karma);

    if(data.summary.submissions.count>0) {
        $("#data-average_submission_karma").text((+data.summary.submissions.computed_karma/+data.summary.submissions.count).toFixed(2));
    } else {
        $("#data-average_submission_karma").text("0");
    }
    $("#data-comment_karma").text(data.summary.comments.computed_karma);
    $("#data-total_comments").text(data.summary.comments.count);
    $("#data-reddit_comment_karma").text(data.summary.comments.all_time_karma);
    if(data.summary.comments.count>0) {
        $("#data-average_comment_karma").text((+data.summary.comments.computed_karma/+data.summary.comments.count).toFixed(2));
    } else {
        $("#data-average_comment_karma").text("0");
    }

    if(data.summary.comments.best.text) {
        $("#data-best_comment").html(data.summary.comments.best.text+" <small><a href='"+data.summary.comments.best.permalink+"'>(permalink)</a></small>");
    }
    if(data.summary.comments.worst.text) {
        $("#data-worst_comment").html(data.summary.comments.worst.text+" <small><a href='"+data.summary.comments.worst.permalink+"'>(permalink)</a></small>");
    }
    if(data.summary.submissions.best.title) {
        $("#data-best_submission").html(data.summary.submissions.best.title+" <small><a href='"+data.summary.submissions.best.permalink+"'>(permalink)</a></small>");
    }
    if(data.summary.submissions.worst.title) {
        $("#data-worst_submission").html(data.summary.submissions.worst.title+" <small><a href='"+data.summary.submissions.worst.permalink+"'>(permalink)</a></small>");
    }

    // Synopsis
    var found_synopsis = false;
    SYNOPSIS_KEYS.forEach(function(d) {
        var row_start = '<div class="row">';
        var row_content = "";
        var row_end = '</div>';
        var once = [];
        if(data.synopsis[d.key]) {
            if((data.synopsis[d.key].data && data.synopsis[d.key].data.length) || (data.synopsis[d.key].data_derived && data.synopsis[d.key].data_derived.length)) {
                found_synopsis = true;
                row_content += '<div class="col-md-4">' + d.label + '</div>';
                row_content += '<div class="col-md-8">';
                
                if(data.synopsis[d.key].data && data.synopsis[d.key].data.length) {
                    if(d.key==="gender" || d.key==="orientation") {
                        once.push(d.key);
                    }
                    data.synopsis[d.key].data.forEach(function(e) {
                        row_content+=wrap_data(d.key, e.value, e.sources, 1);
                    });
                }

                if(data.synopsis[d.key].data_derived && data.synopsis[d.key].data_derived.length && once.indexOf(d.key)===-1) {
                    data.synopsis[d.key].data_derived.forEach(function(e) {
                        row_content+=wrap_data(d.key, e.value, e.sources, 0);
                    });
                }

                row_content += '</div>';
                $("#synopsis-data").append(row_start+row_content+row_end);
            }
        }
    });
    if(!found_synopsis) {
        $("#synopsis-data").html('<div class="col-md-6 alert alert-warning"><p>No synopsis data available.</p></div>');
    }

    // Posts across topics
    curious.sunburst({
        container: "data-topics",
        legend_container: "data-topics_legend",
        data: data.metrics.topic,
        width: 430,
        height: 430,
        margin: {
            top: 0,
            right: 40,
            bottom: 40,
            left: 40
        }
    });

    // Common words
    if(data.metrics.common_words.length>20) {
        $( "#top-words-slider" ).slider({
            value:0,
            min: 0,
            max: 10,
            slide: function( event, ui ) {
                if(ui.value==0) {
                    $( "#top-words-count" ).text("Showing all words. Drag slider below to exclude top words.");    
                } else {
                    $( "#top-words-count" ).text("Excluded top " + ui.value + " words.");
                }
                $("#data-common_words").empty();
                word_cloud(data.metrics.common_words.slice(ui.value));
            }
        });
    } else {
        $( "#top-words-count" ).hide();
        $( "#top-words-slider" ).hide();
    }

    word_cloud(data.metrics.common_words);

    // Metrics chart - Date
    curious.timeseries({
        container: "data-activity_date",
        id: "activity_date_chart",
        data: data.metrics.date.map(function(d) {
            return {
                date:d.date,
                posts:d.comments+d.submissions,
                karma:d.comment_karma+d.submission_karma
            };
        }),
        width: 860,
        height: 430,
        margin: {
            top: 0,
            right: 40,
            bottom: 40,
            left: 40
        },
        tooltips:true,
        x_label: "Date",
        secondary_scale:["karma"]
    });

    // Metrics chart - Weekday
    var weekday_names={"Sun":"Sunday", "Mon":"Monday", "Tue":"Tuesday", "Wed":"Wednesday", "Thu":"Thursday", "Fri":"Friday", "Sat":"Saturday"};
    curious.bar({
        container: "data-activity_weekday",
        data: data.metrics.weekday.map(function(d) {
            return {
                weekday:d.weekday,
                posts:d.comments+d.submissions,
                karma:d.comment_karma+d.submission_karma
            };
        }),
        width: 430,
        height: 430,
        margin: {
            top: 0,
            right: 40,
            bottom: 40,
            left: 40
        },
        tooltips:true,
        x: "weekday",
        x_label: "Day of Week",
        secondary_scale:["karma"],
        tooltip_names: weekday_names
    });

    // Metrics chart - Hour
    var hour_names = ["Midnight", "1 AM", "2 AM", "3 AM", "4 AM", "5 AM", "6 AM", "7 AM", "8 AM", "9 AM", "10 AM", "11 AM", 
                          "Noon", "1 PM", "2 PM", "3 PM", "4 PM", "5 PM", "6 PM", "7 PM", "8 PM", "9 PM", "10 PM", "11 PM"]
    curious.bar({
        container: "data-activity_hour",
        data: data.metrics.hour.map(function(d) {
            return {
                hour:offset_hours>0 ? (24 + d.hour-offset_hours)%24 : (d.hour-offset_hours)%24,
                posts:d.comments+d.submissions,
                karma:d.comment_karma+d.submission_karma
            };
        }).sort(function(a,b) {
            return a.hour - b.hour
        }),
        width: 430,
        height: 430,
        margin: {
            top: 0,
            right: 40,
            bottom: 40,
            left: 40
        },
        tooltips:true,
        x: "hour",
        secondary_scale:["karma"],
        x_label: "Hour of Day (in " + g_user_timezone + ")",
        tooltip_names: hour_names
    });

    // Metrics chart - Posts by Subreddit
    curious.treemap({
        container: "data-posts_by_subreddit",
        data: data.metrics.subreddit,
        width: 840,
        height: 384,
        margin: {
            top: 0,
            right: 0,
            bottom: 0,
            left: 0
        },
        tooltips:true,
        size_col: "posts"
    });

    // Metrics chart - Submissions by Type and Domain
    if(data.summary.submissions.count>0) {
        $("#no-submissions").hide();
        curious.sunburst({
            container: "data-submissions",
            legend_container: "data-submissions_legend",
            data: data.summary.submissions.type_domain_breakdown,
            width: 430,
            height: 430,
            margin: {
                top: 0,
                right: 40,
                bottom: 40,
                left: 40
            },
            breadcrumb_width: { w: 180, h: 30, s: 3, t: 10 }
        });
    }

    // Corpus Statistics
    $("#data-total_word_count").text(data.summary.comments.total_word_count);
    $("#data-unique_word_count").text(data.summary.comments.unique_word_count);
    $("#data-hours_typed").text(data.summary.comments.hours_typed + " hours");
    $("#data-karma_per_word").text(data.summary.comments.karma_per_word);

    $("#user-results-loading").hide();
    $("#user-results").css({opacity:1});

    // Heatmap
    if(data.metrics.recent_activity_heatmap) {
        var heatmap=data.metrics.recent_activity_heatmap;
        var local_last_updated_hour = offset_hours>0 ? (24 + new Date(g_last_updated).getHours()-offset_hours)%24 : (new Date(g_last_updated).getHours()-offset_hours)%24;
        var hours_to_add = 23 - local_last_updated_hour;
        heatmap += Array(hours_to_add+1).join("0");
        heatmap = heatmap.substring(heatmap.length-(60*24));
        
        var heatmap_data = [];
        for(var i=0;i<heatmap.length/24;i++) {
            heatmap_data[i] = [];
            for(var j=0;j<24;j++) {
                heatmap_data[i][j] = parseInt("0x"+heatmap[i*24+j],16);
            }
        }

        curious.heatmap({
            container: "data-heatmap",
            data: heatmap_data,
            width: 500,
            height: 210,
            margin: {
                top: 0,
                right: 0,
                bottom: 20,
                left: 0
            },
            tooltips:true,
            tooltips_msg: function(d) {
                return "<p>" + new Date(new Date().setDate(new Date(g_last_updated).getDate()-(60-d.x))).toLocaleDateString() + "</p>" + hour_names[d.y];
            }
        });
    } else {
        $("#data-heatmap").html('<div class="heatmap-sample"><div class="col-md-6 col-md-offset-3 alert alert-info"><p>Refresh data to see this chart.</p></div></div>');

    }


    // Recent posts and karma
    if(data.metrics.recent_karma && data.metrics.recent_posts && data.metrics.recent_karma.length===data.metrics.recent_posts.length) {
        var recent_activity = data.metrics.recent_karma.slice(1).map(function(d,i) {
            return {
                date: new Date(new Date().setDate(new Date(g_last_updated).getDate()-(60-i-1))).toLocaleDateString(),
                posts: data.metrics.recent_posts[i],
                karma: d
            };
        });


        curious.bar({
            container: "data-recent_activity",
            data: recent_activity,
            width: 500,
            height: 80,
            margin: {
                top: 0,
                right: 0,
                bottom: 0,
                left: 0
            },
            tooltips:true,
            x: "date",
            x_label: "Date",
            secondary_scale:["karma"],
            hide_axes:true
        });
    }

    // Recommendations
    var subreddits_array = flatten_subreddits_tree(data.metrics.subreddit);
    var c = subreddits_array.filter(function(a) {
        return a.average_karma_per_comment;
    }).sort(function(a,b) {
        return a.average_karma_per_comment - b.average_karma_per_comment;
    });

    if(c && c.length>1) {

        $("#data-worst_karma_per_comment").html("<a href=\"http://www.reddit.com/r/" + c[0].name + "\">/r/"+c[0].name+"</a>");
        $("#data-worst_karma_per_comment_subtext").html(
            "<p>" + c[0].average_karma_per_comment + " karma/comment on average</p>" + 
            "<p><small>" + c[0].comment_karma + " total karma over " + c[0].comments + " comments</small></p>"
        );

        $("#data-best_karma_per_comment").html("<a href=\"http://www.reddit.com/r/" + c[c.length-1].name + "\">/r/"+c[c.length-1].name+"</a>");
        $("#data-best_karma_per_comment_subtext").html(
            "<p>" + c[c.length-1].average_karma_per_comment + " karma/comment on average</p>" + 
            "<p><small>" + c[c.length-1].comment_karma + " total karma over " + c[c.length-1].comments + " comments</small></p>"
        );

        $("#no-recommendations").hide();

    } else {
        $("#best-comment-sub-reco").hide();
        $("#worst-comment-sub-reco").hide();
    }

    var s = subreddits_array.filter(function(a) {
        return a.average_karma_per_submission;
    }).sort(function(a,b) {
        return a.average_karma_per_submission - b.average_karma_per_submission;
    });

    if(s && s.length>1) {

        $("#data-worst_karma_per_submission").html("<a href=\"http://www.reddit.com/r/" + s[0].name + "\">/r/"+s[0].name+"</a>");
        $("#data-worst_karma_per_submission_subtext").html(
            "<p>" + s[0].average_karma_per_submission + " karma/submission on average</p>" + 
            "<p><small>" + s[0].submission_karma + " total karma over " + s[0].submissions + " submissions</small></p>"
        );

        $("#data-best_karma_per_submission").html("<a href=\"http://www.reddit.com/r/" + s[s.length-1].name + "\">/r/"+s[s.length-1].name+"</a>");
        $("#data-best_karma_per_submission_subtext").html(
            "<p>" + s[s.length-1].average_karma_per_submission + " karma/submission on average</p>" + 
            "<p><small>" + s[s.length-1].submission_karma + " total karma over " + s[s.length-1].submissions + " submissions</small></p>"
        );

        $("#no-recommendations").hide();

    } else {
        $("#best-post-sub-reco").hide();
        $("#worst-post-sub-reco").hide();
    }

    // Subreddit categorization
    if(data.metrics.subreddit.children && data.metrics.subreddit.children.length) {
        var other_subreddits = data.metrics.subreddit.children.filter(function(d) {
            return d.name==="Other";
        }).shift();
        if(other_subreddits && other_subreddits.children) {
            other_subreddits.children.forEach(function(c) {
                $("#sub-categorize-table-tbody").append(
                    '<tr><td><a href="http://www.reddit.com/r/' + c.name + '/" target="_blank">' + c.name + '</td>' +
                    '<td><a href="#" class="input-editable-category" data-type="typeaheadjs" data-placement="right" data-title="Enter category"' +
                        ' class="editable editable-click" data-original-title="" data-pk="' + c.name + '" title="">Edit category</a></td>' +
                    '<td><a href="#" class="input-editable-subcategory" data-type="typeaheadjs" data-placement="right" data-title="Enter subcategory"' +
                        ' class="editable editable-click" data-original-title="" data-pk="' + c.name + '" data-pk="' + c.name + '"title="">Edit subcategory</a></td>' +
                    '<td><a href="#" class="input-editable-desc" data-type="text" data-pk="' + c.name + '" data-title="Enter description">Edit description</a></td>'
                );
            });
            $.fn.editable.defaults.mode = 'inline';
        
            $('#sub-categorize-table a.input-editable-category').editable({
                value: '',
                name: 'category',
                url: '/categorize',
                params: function(params) {
                    var data = {};
                    data['page_id'] = Math.floor(Date.now());
                    data['page_user'] = g_username;
                    data['subreddit'] = params.pk;
                    data['level_name'] = params.name;
                    data['level_value'] = params.value;
                    return data;
                },
                typeahead: {
                    name: 'category',
                    local: CATEGORIES
                }
            });
            $('#sub-categorize-table a.input-editable-subcategory').editable({
                value: '',
                name: 'subcategory',
                url: '/categorize',
                params: function(params) {
                    var data = {};
                    data['page_id'] = Math.floor(Date.now());
                    data['page_user'] = g_username;
                    data['subreddit'] = params.pk;
                    data['level_name'] = params.name;
                    data['level_value'] = params.value;
                    return data;
                },
                typeahead: {
                    name: 'subcategory',
                    local: SUB_CATEGORIES
                }
            });
            $('#sub-categorize-table a.input-editable-desc').editable({
                value: '',
                name: 'description',
                url: '/categorize',
                params: function(params) {
                    var data = {};
                    data['page_id'] = Math.floor(Date.now());
                    data['page_user'] = g_username;
                    data['subreddit'] = params.pk;
                    data['level_name'] = params.name;
                    data['level_value'] = params.value;
                    return data;
                },
            });
        } else {
            $("#sub-categorize-table").html('<div class="col-md-6 alert alert-success"><p>All your subreddits have been categorized. You\'re all set!</p></div>')
        }
        
    }

}

function home_init() {
    $( "#process_form" ).submit(function( event ) {
        $( "#go" ).button("loading");
        event.preventDefault();
        var $form = $( this ),
        username = $form.find( "input[name='username']" ).val();
        if(!username) return;
        g_username = username;
        $.ajax({
            url: "/check/" + username,
            type: "GET",
        }).done(function(response) {
            if(response=="OK") {
                //User exists in local DB, forward to profile page
                window.location.href = "/u/"+username;
            } else {
                //No dice, retrieve data from API
                get_data(username);
            }
        });
    });
}

function user_init() {
    g_base_results = $("#user-results").html();
    populate_results(results);
    $(".feedback .correct, .feedback .incorrect").click(function() {
        key = $(this).data("key");
        value = $(this).data("value");
        feedback = $(this).data("feedback");
        send_feedback(key, value, feedback);
        feedback_container = $(this).parent();
        feedback_container.html("<span class='thanks'>Thanks!</span>");
        feedback_container.fadeOut(1000,function() {
            $(this).html(feedback?"<i class='fa fa-check correct_done'></i>":"<i class='fa fa-close incorrect_done'></i>");
        }).fadeIn(200);
        return false;
    });

    $("#go").click(function(event) {
        $("#go").button("loading");
        event.preventDefault();
        if(!g_username) return;
        get_data(g_username);
    });
}

