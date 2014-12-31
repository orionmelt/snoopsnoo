var base_results = "";
var username = "";

var FULL_WIDTH=860;
var HALF_WIDTH=430;

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

function wrap_data(key, text, sources) {
    var source_links = "";
    /*sources && sources.forEach(function (s) {
        source_links += " <a href=\""+s+"\">#</i></a> ";
    });*/
    return  '<span class="data-block">' + 
                '<span class="content">' + text + 
                '</span>' + 
                '<span class="feedback">' +
                    '<a class="correct" data-key="' + key + '" data-value="' + text + '" data-feedback="1" title="This is correct" href="#">' + 
                        '<i class="fa fa-check-circle-o"></i>' + 
                    '</a> ' + 
                    '<a class="incorrect" data-key="' + key + '" data-value="' + text + '" data-feedback="0" title="This is incorrect/gibberish" href="#">' +
                        '<i class="fa fa-times-circle-o"></i>' +
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
    var data = JSON.parse(results);
    username = data.username;

    // Stats
    $("#data-signup_date").text(data.stats.basic.signup_date);
    $("#data-signup_date_text").text(data.stats.basic.signup_date_text);

    $("#data-first_post_date").text(data.stats.basic.first_post_date);
    $("#data-first_post_date_text").text(data.stats.basic.first_post_date_text);

    $("#data-lurk_streak_duration").text(data.stats.basic.lurk_streak["duration"]);
    $("#data-lurk_streak_dates").text(data.stats.basic.lurk_streak["date1"] + " to " + data.stats.basic.lurk_streak["date2"]);

    if(data.stats.basic.submissions.gilded>0) {
        $("#data-submissions_gilded").html("<a href='http://www.reddit.com/user/" + data.username + "/gilded' target='_blank'>" + data.stats.basic.submissions.gilded + " submissions</a>");
    } else {
        $("#data-submissions_gilded").text(data.stats.basic.submissions.gilded + " submissions");
    }

    if(data.stats.basic.comments.gilded>0) {
        $("#data-comments_gilded").html("<a href='http://www.reddit.com/user/" + data.username + "/gilded' target='_blank'>" + data.stats.basic.comments.gilded + " comments</a>");
    } else {
        $("#data-comments_gilded").text(data.stats.basic.comments.gilded + " comments");
    }

    $("#data-link_karma").text(data.stats.basic.link_karma);
    $("#data-total_submissions").text(data.stats.basic.submissions.count);
    if(data.stats.basic.submissions.count>0) {
        $("#data-average_link_karma").text((+data.stats.basic.link_karma/+data.stats.basic.submissions.count).toFixed(2));
    } else {
        $("#data-average_link_karma").text("0");
    }
    $("#data-comment_karma").text(data.stats.basic.comment_karma);
    $("#data-total_comments").text(data.stats.basic.comments.count);
    if(data.stats.basic.comments.count>0) {
        $("#data-average_comment_karma").text((+data.stats.basic.comment_karma/+data.stats.basic.comments.count).toFixed(2));
    } else {
        $("#data-average_comment_karma").text("0");
    }
    if(data.stats.basic.comments.best.text) {
        $("#data-best_comment").html(data.stats.basic.comments.best.text+" <small><a href='"+data.stats.basic.comments.best.permalink+"'>(permalink)</a></small>");
    }
    if(data.stats.basic.comments.worst.text) {
        $("#data-worst_comment").html(data.stats.basic.comments.worst.text+" <small><a href='"+data.stats.basic.comments.worst.permalink+"'>(permalink)</a></small>");
    }
    if(data.stats.basic.submissions.best.title) {
        $("#data-best_submission").html(data.stats.basic.submissions.best.title+" <small><a href='"+data.stats.basic.submissions.best.permalink+"'>(permalink)</a></small>");
    }
    if(data.stats.basic.submissions.worst.title) {
        $("#data-worst_submission").html(data.stats.basic.submissions.worst.title+" <small><a href='"+data.stats.basic.submissions.worst.permalink+"'>(permalink)</a></small>");
    }

    $("#data-total_word_count").text(data.stats.basic.words_in_posts.total_word_count);
    $("#data-unique_word_count").text(data.stats.basic.words_in_posts.unique_word_count);
    $("#data-hours_typed").text(data.stats.basic.words_in_posts.hours_typed + " hours");
    $("#data-karma_per_word").text(data.stats.basic.words_in_posts.karma_per_word);

    // Synopsis
    for(var key in data.about) {
        if(data.about.hasOwnProperty(key)) {
            if(data.about[key]) {
                if(typeof data.about[key] == "string") {
                    $("#data-"+key).append(wrap_data(key, data.about[key]));
                } else if($.isArray(data.about[key])) {
                    if(data.about[key].length>0) {
                        data.about[key].forEach(function(d) {
                            $("#data-"+key).append(wrap_data(key, d["value"], d["sources"]));
                        });
                    } else {
                        $("#data-container-"+key).hide();
                    }
                    
                } else if(typeof data.about[key] == "object") {
                    if(data.about[key].core && data.about[key].core.length>0) {
                        data.about[key].core.forEach(function(d) {
                            $("#data-"+key).append(wrap_data(key, d["value"], d["sources"]));
                        });    
                    } else {
                        $("#data-container-"+key).hide();
                    }
                }
            } else {
                $("#data-container-"+key).hide();
            }
        }
    }

    for(var key in data.about.derived_attributes) {
        if(data.about.derived_attributes.hasOwnProperty(key)) {
            if(data.about.derived_attributes[key]) {
                if(typeof data.about.derived_attributes[key] == "string") {
                    $("#data-derived-"+key).append(wrap_data(key, data.about.derived_attributes[key]));
                } else if($.isArray(data.about.derived_attributes[key])) {
                    if(data.about.derived_attributes[key].length>0) {
                        data.about.derived_attributes[key].forEach(function(d) {
                            $("#data-derived-"+key).append(wrap_data(key, d[0]));
                        });
                    } else {
                        $("#data-container-derived-"+key).hide();
                    }
                    
                } else if(typeof data.about.derived_attributes[key] == "object") {
                    if(data.about.derived_attributes[key].core && data.about.derived_attributes[key].core.length>0) {
                        data.about.derived_attributes[key].core.forEach(function(d) {
                            $("#data-derived-"+key).append(wrap_data(key, d[0]));
                        });    
                    } else {
                        $("#data-container-derived-"+key).hide();
                    }
                }
            } else {
                $("#data-container-derived-"+key).hide();
            }
        }
    }

    // Update metrics chart - Date
    curious.timeseries({
        container: "data-activity_date",
        id: "activity_date_chart",
        data: data.stats.metrics.date.map(function(d) {
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

    // Update metrics chart - Weekday
    var weekday_names={"Sun":"Sunday", "Mon":"Monday", "Tue":"Tuesday", "Wed":"Wednesday", "Thu":"Thursday", "Fri":"Friday", "Sat":"Saturday"};
    curious.bar({
        container: "data-activity_weekday",
        data: data.stats.metrics.weekday.map(function(d) {
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

    // Update metrics chart - Hour
    var hour_names = ["Midnight", "1 AM", "2 AM", "3 AM", "4 AM", "5 AM", "6 AM", "7 AM", "8 AM", "9 AM", "10 AM", "11 AM", 
                          "Noon", "1 PM", "2 PM", "3 PM", "4 PM", "5 PM", "6 PM", "7 PM", "8 PM", "9 PM", "10 PM", "11 PM"]
    curious.bar({
        container: "data-activity_hour",
        data: data.stats.metrics.hour.map(function(d) {
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

    // Update metrics chart - Treemap
    curious.treemap({
        container: "data-posts_by_subreddit",
        data: data.stats.metrics.subreddit,
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

    // Update topics chart - Sunburst
    curious.sunburst({
        container: "data-topics",
        legend_container: "data-topics_legend",
        data: data.stats.metrics.topic,
        width: 430,
        height: 430,
        margin: {
            top: 0,
            right: 40,
            bottom: 40,
            left: 40
        }
    });

    if(data.stats.common_words.length>20) {
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
                word_cloud(data.stats.common_words.slice(ui.value));
            }
        });
    } else {
        $( "#top-words-count" ).hide();
        $( "#top-words-slider" ).hide();
    }

    word_cloud(data.stats.common_words);

    // Update submissions chart - Sunburst
    if(data.stats.basic.submissions.count>0) {
        $("#no-submissions").hide();
        curious.sunburst({
            container: "data-submissions",
            legend_container: "data-submissions_legend",
            data: data.stats.metrics.submissions,
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


    $("#user-results-loading").hide();
    $("#user-results").css({opacity:1});
}

function index_setup() {
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
                        $( "#error-message" ).text("Sorry, an unexpected error has occurred.");
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
                });


            }
        });
    });
}

function user_setup() {
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