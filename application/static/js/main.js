var base_results = "";
var username = "";
var show_source = false;

var FULL_WIDTH=860;
var HALF_WIDTH=430;

var synopsis_keys = [
    {label: "you are", key:"gender"},
    {label: "you are", key:"orientation"},
    {label: "you are in a relationship with your", key:"relationship_partner"}, 
    {label: "you live(d)", key:"places_lived"}, 
    {label: "you grew up", key:"places_grew_up"},
    {label: "people in your family", key:"family_members"}, 
    {label: "you have these pets:", key:"pets"}, 
    {label: "you like", key:"favorites"}, 
    {label: "you are", key:"attributes"},
    {label: "you have", key:"possessions"}, 
    {label: "you <span class=\"likely\">may have</span> lived in", key:"locations"}, 
    {label: "you like to watch", key:"tv_shows"}, 
    {label: "you like", key:"interests"}, 
    {label: "you like playing", key:"games"}, 
    {label: "sports and teams you like:", key:"sports"}, 
    {label: "you like listening to", key:"music"}, 
    {label: "you use", key:"drugs"}, 
    {label: "you like to read", key:"books"}, 
    {label: "you like", key:"celebs"}, 
    {label: "you are interested in", key:"business"}, 
    {label: "you like", key:"entertainment"},
    {label: "you are interested in", key:"science"}, 
    {label: "you are interested in", key:"tech"}, 
    {label: "you are interested in", key:"lifestyle"}, 
    {label: "you are interested in", key:"others"}, 
    {label: "you have", key:"gadget"}, 
    {label: "you are", key:"political_view"}, 
    {label: "you are", key:"physical_characteristics"}, 
    {label: "you are", key:"religion"}
];

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
                "date": data.stats.basic.signup_date,
                "humanized": data.stats.basic.signup_date_text,
            },
            "first_post_date": {
                "date": data.stats.basic.first_post_date,
                "humanized": data.stats.basic.first_post_date_text
            },
            "lurk_period": {
                "from": data.stats.basic.lurk_streak.date1,
                "to": data.stats.basic.lurk_streak.date2,
                "humanized": data.stats.basic.lurk_streak.duration
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
                "uniq_word_count": data.stats.basic.words_in_posts.unique_word_count, //Fix to exclude words in submissions
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
            "words": data.stats.common_words
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
                    s["extra_data"] = data.about[key].more;
                } else if(typeof data.about[key] === "object") {

                } else {
                    //What could this be?
                }
            }
            if(data.about["derived_attributes"] && data.about["derived_attributes"][d_key]) {
                if(typeof data.about["derived_attributes"][d_key] === "string") {
                    s["derived_data"] = {
                        "value": data.about["derived_attributes"][d_key],
                        "count": null,
                        "sources": null
                    }
                } else if($.isArray(data.about["derived_attributes"][d_key])) {
                    if(data.about["derived_attributes"][d_key].length) {
                        s["derived_data"] = [];
                        data.about["derived_attributes"][d_key].forEach(function(d) {
                             s["derived_data"].push({
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

            if(s.data || s.derived_data) {
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
                    s["derived_data"] = [];
                    data.about["derived_attributes"][key].forEach(function(d) {
                         s["derived_data"].push({
                            "value": d[0],
                            "count": d[1],
                            "sources": null
                        });
                    });
                }
            }
            if(s.derived_data) v2.synopsis[key]=s;
        }
    }

    // Fix Lifestyle/Drugs issue
    if(v2.synopsis.drugs) {
        v2.synopsis.lifestyle.data = v2.synopsis.lifestyle.data.filter(function(d) {
            if(!v2.synopsis.drugs.data.indexOf(d.value)) return d;
        });
    }
    return v2;
}

function send_feedback(key, value, feedback) {
    url = "/feedback?u="+username+"&k="+key+"&v="+value+"&f="+feedback;
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
    show_source && sources && sources.forEach(function (s) {
        source_links += " <a href=\""+s+"\">#</i></a> ";
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
                    source_links + 
                '</span>' + 
            '</span>';
}

function word_cloud(words_array) {
    var data = JSON.parse(JSON.stringify(words_array));
    var fill = d3.scale.category20();
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
    $("#user-results").html(base_results);
    var data = convert_to_v2(JSON.parse(results));
    username = data.username;
    if(location.search.substring(1)==="sources") show_source=true;
    if(show_source) {
        console.log(JSON.parse(results));
        console.log(data);
    }

    // Summary
    $("#data-signup_date").text(data.summary.signup_date.date);
    $("#data-signup_date_humanized").text(data.summary.signup_date.humanized);

    $("#data-first_post_date").text(data.summary.first_post_date.date);
    $("#data-first_post_date_humanized").text(data.summary.first_post_date.humanized);

    $("#data-lurk_period_humanized").text(data.summary.lurk_period.humanized);
    $("#data-lurk_period_dates").text(data.summary.lurk_period.from + " to " + data.summary.lurk_period.to);

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
    synopsis_keys.forEach(function(d) {
        var row_start = '<div class="row">';
        var row_content = "";
        var row_end = '</div>';
        var once = [];
        if(data.synopsis[d.key]) {
            if((data.synopsis[d.key].data && data.synopsis[d.key].data.length) || (data.synopsis[d.key].derived_data && data.synopsis[d.key].derived_data.length)) {
                row_content += '<div class="col-md-3">' + d.label + '</div>';
                row_content += '<div class="col-md-9">';
                
                if(data.synopsis[d.key].data && data.synopsis[d.key].data.length) {
                    if(d.key==="gender" || d.key==="orientation") {
                        once.push(d.key);
                    }
                    data.synopsis[d.key].data.forEach(function(e) {
                        row_content+=wrap_data(d.key, e.value, e.sources, 1);
                    });
                }

                if(data.synopsis[d.key].derived_data && data.synopsis[d.key].derived_data.length && once.indexOf(d.key)===-1) {
                    data.synopsis[d.key].derived_data.forEach(function(e) {
                        row_content+=wrap_data(d.key, e.value, e.sources, 0);
                    });
                }

                row_content += '</div>';
                $("#synopsis-data").append(row_start+row_content+row_end);
            }
        }
    });

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
    if(data.metrics.words.length>20) {
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
                word_cloud(data.metrics.words.slice(ui.value));
            }
        });
    } else {
        $( "#top-words-count" ).hide();
        $( "#top-words-slider" ).hide();
    }

    word_cloud(data.metrics.words);

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
                hour:d.hour,
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
        x: "hour",
        secondary_scale:["karma"],
        x_label: "Hour of Day (in UTC)",
        tooltip_names: hour_names
    });

    // Metrics chart - Posts by Subreddit
    curious.treemap({
        container: "data-posts_by_subreddit",
        data: data.metrics.subreddit,
        width: 860,
        height: 430,
        margin: {
            top: 0,
            right: 40,
            bottom: 40,
            left: 40
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

    // Text in Comments
    $("#data-total_word_count").text(data.summary.comments.total_word_count);
    $("#data-unique_word_count").text(data.summary.comments.uniq_word_count);
    $("#data-hours_typed").text(data.summary.comments.hours_typed + " hours");
    $("#data-karma_per_word").text(data.summary.comments.karma_per_word);

    $("#user-results-loading").hide();
    $("#user-results").css({opacity:1});
}

function home_init() {
    $( "#process_form" ).submit(function( event ) {
        $( "#go" ).button("loading");
        event.preventDefault();
        var $form = $( this ),
        username = $form.find( "input[name='username']" ).val();

        //Check if user exists in local DB
        $.ajax({
            url: "/cu/" + username,
            type: "GET",
        }).done(function(response) {
            if(response=="OK") {
                //User exists in local DB, forward to profile page
                window.location.href = "/u/"+username;
            } else {
                //No dice, retrieve data from API
                $.ajax({
                    url: "https://sender.blockspring.com/api_v1/blocks/de18d68b50728daf9b35fcc49010a2fd?api_key=d1b2e14d5b005465cfe3c83976a9240a",
                    type: "POST",
                    data: { username: username},
                    crossDomain: true
                }).done(function(response){
                    //Data is here from API
                    $( "#go" ).button("reset");
                    console.log(response);
                    if(!response.error && response.results) {
                        //Update data in local DB
                        $.ajax({
                            url: "/update_user",
                            type: "POST",
                            contentType: "application/json",
                            data: response.results,
                        }).done(function(response) {
                            if(response=="OK") {
                                //Now user exists in local DB, forward to profile page
                                window.location.href = "/u/"+username;
                            } else if(response=="EMPTY") {
                                $( "#error-message" ).text("No data available.");
                                $( "#error" ).show();
                                var error_object = {"username":username, "error_type": "empty", "error_message":response.error};
                                log_error(error_object);
                            }
                        });
                    } else if(response.error) {
                        //Something went wrong
                        $( "#error-message" ).text("Sorry, an unexpected error has occurred. Please try again in a few minutes.");
                        $( "#error" ).show();
                        var error_object = {"username":username, "error_type": "server_error", "error_message":response.error};
                        log_error(error_object);
                        //TODO - Update response.error in DB 
                    } else {
                        //Server too busy
                        $( "#error-message" ).text("Server too busy. Please try again in a few minutes.");
                        $( "#error" ).show();
                        var error_object = {"username":username, "error_type": "timeout", "error_message":response.error};
                        log_error(error_object);
                    }
                }).fail(function(jqXHR, status) {
                    console.log(jqXHR, status);
                });


            }
        });
    });
}

function user_init() {
    base_results = $("#user-results").html();
    populate_results(results);
    $(".feedback .correct, .feedback .incorrect").click(function() {
        key = $(this).data("key");
        value = $(this).data("value");
        feedback = $(this).data("feedback");
        send_feedback(key, value, feedback);
        _f = $(this).parent();
        _f.html("<span class='thanks'>Thanks!</span>");
        _f.fadeOut(1000,function() {
            $(this).html(feedback?"<i class='fa fa-check correct_done'></i>":"<i class='fa fa-close incorrect_done'></i>");
        }).fadeIn(200);
        return false;
    });
}