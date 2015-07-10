!function(){
    var curious={version:"0.1"};

    curious._any = function(needle, haystack) {
        for (var h=0; h<haystack.length; h++) {
            for (var n=0; n<needle.length; n++) {
                if(needle[n]==haystack[h]) return true;
            }
        }
        return false;
    }
    
    // Draws a timeseries chart. A field named "date" is required and will be used for the x-axis.
    curious.timeseries = function(options) {
        var options = options || {};
        var container = "#"+options.container;
        var data = JSON.parse(JSON.stringify(options.data));
        var width = options.width;
        var height = options.height;
        var margin = options.margin;
        var color = options.color || d3.scale.category10();
        var interpolate = options.interpolate || "";
        var tooltips = options.tooltips || false;
        var secondary_scale = options.secondary_scale || [];
        var x_label = options.x_label || "Date";

        // If data doesn't contain a "date" field, write error message to log
        if (!data.length || !("date" in data[0])) console.log("Error: Data doesn't contain field named 'date'.");

        // Let's just assume that all our dates are of the format YYYY-MM-DD
        var parseDate = d3.time.format("%Y-%m-%d").parse;

        // Create x and y scales
        var x = d3.time.scale().range([0, width-margin.right]),
            y = d3.scale.linear().range([height, 0]),
            ys = (secondary_scale && secondary_scale.length>0)? d3.scale.linear().range([height, 0]) : null;

        
        // Format dates using d3.time
        data.forEach(function(d) {
            d.date = parseDate(d.date);
        });
        
        // Create SVG canvas
        var svg = d3.select(container)
        .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
        .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        // Get all y-axis data series
        color.domain(d3.keys(data[0]).filter(function(key) { return key !== "date"; }));

        var series_values = color.domain().map(function(name) {
            return {
                name: name,
                values: data.map(function(d) {
                    return {date: d.date, value: +d[name]};
              })
            };
        });

        // Declare x and y axis functions
        var x_axis_fn = d3.svg.axis()
            .scale(x)
            .orient("bottom");

        var y_axis_fn = d3.svg.axis()
            .scale(y)
            .orient("left")
            .tickFormat(d3.format(".2s"));

        var ys_axis_fn = (secondary_scale && secondary_scale.length>0) ? (d3.svg.axis().scale(ys).orient("right").tickFormat(d3.format(".2s"))) : null;

        // Line functions that create an SVG path
        var line = d3.svg.line()
            .interpolate(interpolate)
            .x(function(d) { return x(d.date); })
            .y(function(d) { return y(d.value); });

        if(secondary_scale && secondary_scale.length>0) {
            var line_secondary = d3.svg.line()
                .interpolate(interpolate)
                .x(function(d) { return x(d.date); })
                .y(function(d) { return ys(d.value); });
        }

        // Map x and y domain values
        x.domain(d3.extent(data, function(d) { return d.date; }));

        y_max = d3.max(series_values.filter(function(d) { return secondary_scale.indexOf(d.name)<0;}), function(d) { return d3.max(d.values, function(v) { return v.value; }); });
        ys_max = d3.max(series_values.filter(function(d) { return secondary_scale.indexOf(d.name)>-1;}), function(d) { return d3.max(d.values, function(v) { return v.value; }); });

        y_min = d3.min(series_values.filter(function(d) { return secondary_scale.indexOf(d.name)<0;}), function(d) { return d3.min(d.values, function(v) { return v.value; }); });
        ys_min = d3.min(series_values.filter(function(d) { return secondary_scale.indexOf(d.name)>-1;}), function(d) { return d3.min(d.values, function(v) { return v.value; }); });

        y_max += y_max*0.1;
        ys_max += ys_max*0.1;

        y_min -= y_min*0.1;
        ys_min -= ys_min*0.1;

        y.domain([
            y_min,
            y_max
        ]);

        if(secondary_scale && secondary_scale.length>0) {
            ys.domain([
                ys_min,
                ys_max
            ]);
        }

        // Attach x and y axes to SVG
        var x_axis = svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(x_axis_fn);

        var y_axis = svg.append("g")
            .attr("class", "y axis")
            .call(y_axis_fn);
                    

        if(secondary_scale && secondary_scale.length>0) {
            var y_axis_secondary = svg.append("g")
                .attr("class", "y axis")
                .attr("transform", "translate(" + (width-margin.right) + " ,0)")
                .call(ys_axis_fn);
        }


        // Add label to x axis
        x_axis.append("g").append("text")
            .attr("transform", function() { return "translate(0,0)"; })
            .attr("x", width/2)
            .attr("y", 30)
            .attr("dy", ".71em")
            .style("text-anchor", "middle")
            .attr("font-weight", "bold")
            .text(x_label);

        // Add legend to y axis
        y_axis.selectAll(".legend")
            .data(series_values.filter(function(d) { return secondary_scale.indexOf(d.name)<0;}))
        .enter().append("g").append("text")
            .attr("transform", function(d, i) { return "translate(0," + i*20 + ")"; })
            .attr("x", 6)
            .attr("y", 6)
            .attr("dy", ".71em")
            .style("text-anchor", "start")
            .style("fill", function(d) { return color(d.name); })
            .text(function(d) { return "◼ "+d.name; });

        if(secondary_scale && secondary_scale.length>0) {
            y_axis_secondary.selectAll(".legend")
                .data(series_values.filter(function(d) { return secondary_scale.indexOf(d.name)>-1;}))
            .enter().append("g")
                .append("text")
                .attr("transform", function(d, i) { return "translate(0," + i*20 + ")"; })
                .attr("x", -6)
                .attr("y", 6)
                .attr("dy", ".71em")
                .style("text-anchor", "end")
                .style("fill", function(d) { return color(d.name); })
                .text(function(d) { return "◼ "+d.name; });
        }
        
        // For each series, create group element...
        var series = svg.selectAll(".series")
            .data(series_values)
        .enter().append("g")
            .attr("class", "series");

        // ... and a line path
        series.append("path")
            .attr("class", "line")
            .attr("d", function(d) { return secondary_scale.indexOf(d.name)<0 ? line(d.values) : line_secondary(d.values); })
            .style("stroke", function(d) { return color(d.name); });
        

        // If tooltips are enabled...
        if(tooltips) {
            // Create tip object
            var tip = d3.tip()
                .attr('class', 'd3-tip')
                .offset([-10, 0])
                .html(function(d) {
                    return "<p>" +  d3.time.format("%B %Y")(d.date) + "</p>" + d.value + " " + this.parentNode.__data__.name.replace("_"," ");
                });

            svg.call(tip);

            // Create a small, translucent circle over each plotted point
            var point = series.append("g")
                .attr("class", "line-point");

            point.selectAll('.tip-point')
                .data(function(d){ return d.values})
            .enter().append('circle')
                .attr("cx", function(d) { return x(d.date); })
                .attr("cy", function(d) { return secondary_scale.indexOf(this.parentNode.__data__.name)<0 ? y(d.value) : ys(d.value); })
                .attr("r", 4)
                .style("fill", function(d) { return color(this.parentNode.__data__.name); })
                .style("fill-opacity", "0.5")
                .on('mouseenter', tip.show)
                .on('mouseleave', tip.hide);
        }
    };

    curious.bar = function(options) {
        var options = options || {};
        var container = "#"+options.container;
        var data = JSON.parse(JSON.stringify(options.data));
        var width = options.width;
        var height = options.height;
        var margin = options.margin;
        var color = options.color || d3.scale.category10();
        var tooltips = options.tooltips || false;
        var x_col = options.x;
        var secondary_scale = options.secondary_scale || [];
        var tooltip_names = options.tooltip_names || null;
        var x_label = options.x_label;
        var hide_axes = options.hide_axes || false;

        // Create x and y scales
        var x0 = d3.scale.ordinal().rangeRoundBands([0, width-margin.left], .1),
            x1 = d3.scale.ordinal(),
            y = d3.scale.linear().range([height, 0]),
            ys = (secondary_scale && secondary_scale.length>0)? d3.scale.linear().range([height, 0]) : null;

        // Create SVG canvas
        var svg = d3.select(container)
        .append("svg")
            .attr("viewBox", "0 0 " + (width + margin.left + margin.right) + " " + (height + margin.top + margin.bottom))
            .attr("preserveAspectRatio", "xMidYMid")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
        .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        // Get all y-axis data series
        var series_names = d3.keys(data[0]).filter(function(key) { return key !== x_col; });

        color.domain(series_names);

        data.forEach(function(d) {
            d.series_values = series_names.map(function(name) { return {name: name, value: +d[name]}; });
        });

        // Declare x and y axis functions
        var x_axis_fn = d3.svg.axis()
            .scale(x0)
            .orient("bottom");

        var y_axis_fn = d3.svg.axis()
            .scale(y)
            .orient("left")
            .tickFormat(d3.format(".2s"));

        var ys_axis_fn = (secondary_scale && secondary_scale.length>0) ? (d3.svg.axis().scale(ys).orient("right").tickFormat(d3.format(".2s"))) : null;

        // Map x and y domain values
        x0.domain(data.map(function(d) {return d[x_col];}));
        x1.domain(series_names).rangeRoundBands([0, x0.rangeBand()]);

        y_max = d3.max(data, function(d) { return d3.max(d.series_values, function(d) { if(secondary_scale.indexOf(d.name)<0) return d.value; }); });
        ys_max = d3.max(data, function(d) { return d3.max(d.series_values, function(d) { if(secondary_scale.indexOf(d.name)>-1) return d.value; }); })

        y_max += y_max*0.1;
        ys_max += ys_max*0.1;

        y.domain([0, y_max]);
        ys.domain([0, ys_max]);
        
        // Attach x and y axes to SVG
        if(!hide_axes) {
            var x_axis = svg.append("g")
                .attr("class", "x axis")
                .attr("transform", "translate(0," + height + ")")
                .call(x_axis_fn);

            var y_axis = svg.append("g")
                .attr("class", "y axis")
                .call(y_axis_fn);
                        

            if(secondary_scale && secondary_scale.length>0) {
                var y_axis_secondary = svg.append("g")
                    .attr("class", "y axis")
                    .attr("transform", "translate(" + (width-margin.right) + " ,0)")
                    .call(ys_axis_fn);
            }

            // Add label to x axis
            x_axis.append("g").append("text")
                .attr("transform", function() { return "translate(0,0)"; })
                .attr("x", width/2)
                .attr("y", 30)
                .attr("dy", ".71em")
                .style("text-anchor", "middle")
                .attr("font-weight", "bold")
                .text(x_label);
            
            // Add legend to y axis
            y_axis.selectAll(".legend")
                .data(series_names.filter(function(d) { return secondary_scale.indexOf(d)<0;}))
            .enter().append("g").append("text")
                .attr("transform", function(d, i) { return "translate(0," + i*20 + ")"; })
                .attr("x", 6)
                .attr("y", 6)
                .attr("dy", ".71em")
                .style("text-anchor", "start")
                .style("fill", function(d) { return color(d); })
                .text(function(d) { return "◼ "+d; });

            if(secondary_scale && secondary_scale.length>0) {
                y_axis_secondary.selectAll(".legend")
                    .data(series_names.filter(function(d) { return secondary_scale.indexOf(d)>-1;}))
                .enter().append("g")
                    .append("text")
                    .attr("transform", function(d, i) { return "translate(0," + i*20 + ")"; })
                    .attr("x", -6)
                    .attr("y", 6)
                    .attr("dy", ".71em")
                    .style("text-anchor", "end")
                    .style("fill", function(d) { return color(d); })
                    .text(function(d) { return "◼ "+d; });
            }
        }
        
        // For each series, create group element...
        var series = svg.selectAll(".series")
            .data(data)
        .enter().append("g")
            .attr("class", "series")
            .attr("name", function(d) { return d[x_col]; })
            .attr("transform", function(d) { return "translate(" + x0(d[x_col]) + ",0)"; });

        
        // ... and bars
        var rect = series.selectAll("rect")
            .data(function(d) { return d.series_values; })
        .enter().append("rect")
            .attr("width", x1.rangeBand())
            .attr("x", function(d) { return x1(d.name); })
            .attr("y", function(d) { return secondary_scale.indexOf(d.name)<0 ? y(d.value) : ys(d.value); })
            .attr("height", function(d) { return height - (secondary_scale.indexOf(d.name)<0 ? y(d.value) : ys(d.value)); })
            .style("fill", function(d) { return color(d.name); });

        // If tooltips are enabled...
        if(tooltips) {
            // Create tip object
            var tip = d3.tip()
                .attr('class', 'd3-tip')
                .offset([-10, 0])
                .html(function(d) {
                    return "<p>" + (tooltip_names ? tooltip_names[this.parentNode.__data__[x_col]] : this.parentNode.__data__[x_col]) + "</p>" + d.value + " " + d.name;
                });

            svg.call(tip);

            rect
                .on('mouseenter', tip.show)
                .on('mouseleave', tip.hide);
        }
    };

    /*
    // Draws a circlepack
    curious.circlepack = function(options) {
        var options = options || {};
        var container = "#"+options.container;
        var data = JSON.parse(JSON.stringify(options.data));
        var width = options.width;
        var diameter = options.diameter;
        var margin = options.margin;
        var color = options.color || d3.scale.category10();
        var tooltips = options.tooltips || false;
        var values = options.values || {fields:[], label:""};

        // Create SVG canvas
        var svg = d3.select(container)
        .append("div")
            .style("position", "relative")
            .style("width", width + "px")
            .style("height", diameter + "px")
            .style("top", margin.top + "px")
            .style("display", "inline-block")
        .append("svg")
            .attr("viewBox", "0 0 " + width + " " + diameter)
            .attr("preserveAspectRatio", "xMidYMid")
            .attr("width", width)
            .attr("height", diameter)
            .attr("top", margin.top + "px")
            .append("g")
            .attr("transform", "translate(" + width / 2 + "," + diameter / 2 + ")");
        
        var pack = d3.layout.pack()
            .size([diameter - 4, diameter - 4])
            .padding(10)
            .value(function(d) {
                value = 0;
                for(var i=0; i<values.fields.length; i++) {
                    value += +d[values.fields[i]];
                }
                return value;
            });

        var focus = data,
            nodes = pack.nodes(data),
            view;

        // Create tip object
        var tip = d3.tip()
            .attr('class', 'd3-tip')
            .offset([-10, 0])
            .html(function(d) {
                return d.children?"<strong>"+d.name+"</strong>":"<p>/r/"+d.name+"</p>"+d.value+" "+values.label;
            });

        svg.call(tip);

        var g = svg.selectAll(".c")
            .data(nodes)
        .enter().append("g")
            .attr("class", function(d) { return d.parent ? d.children ? "node" : "node node--leaf" : "node node--root"; })
            .on("click", function(d) { if (tooltips) tip.hide(); if (focus !== d) zoom(d), d3.event.stopPropagation(); });

        // If tooltips are enabled...
        if(tooltips) g.on('mouseenter', tip.show).on('mouseleave', tip.hide);
        
        var circle = g.append("circle")
            .style("fill", function(d) {
                return d.parent ? d.children ? color(d.name) : color(d.parent.name) : "#bbb";
            })
            .style("fill-opacity", function(d) { return d.children ? "0.25" : "1.0"; })
        
        var text = g.append("text")
            .style("background", "white")
            .style("text-anchor", "middle")
            .style("fill-opacity", function(d) { return d.children == null ? 1 : 0; })
            .style("display", function(d) {
                var n=d.name.substring(0, d.r / 3);
                return (n.length<d.name.length || d.children) ? "none" : "inline";
            })
            .text(function(d) { return d.name; });

        var node = svg.selectAll("circle,text");

        d3.select(container)
            .on("click", function() {
                if (tooltips) tip.hide();
                zoom(data);
            });

        zoomTo([data.x, data.y, data.r * 2 + margin.left]);

        function zoom(d) {

            var focus0 = focus; focus = d;

            var transition = text.transition()
                .duration(d3.event.altKey ? 7500 : 750)
                .tween("zoom", function(d) {
                    var i = d3.interpolateZoom(view, [focus.x, focus.y, focus.r * 2 + margin.left]);
                    return function(t) { zoomTo(i(t)); };
                });

            transition
                .style("fill-opacity", function(d) { return d.parent === focus ? 1 : 0; })
                .each("start", function(d) {
                    
                })
                .each("end", function(d) {
                    //console.log(this, this.parentNode);
                    //console.log(d.r);
                    //console.log()
                    //this.style.fontSize = this.parentNode.firstChild.getAttribute("r")>25 ? 12 : 0;
                    //var n=d.name.substring(0, +this.parentNode.firstChild.getAttribute("r") / 3);
                    //this.style.display = (n.length<d.name.length || d.children) ? "none" : "inline";
                    
                    //if(d.name=="pakistan") console.log(d);
                    //console.log(d);
                    
                })
                //.each("end", function(d) { this.style.display = "none"; });
                //.each("start", function(d) { if (d.parent === focus) this.style.display = "inline"; })
                ////.each("start", function(d) { if (d.parent !== focus) this.style.display = "inline"; })
                //.each("end", function(d) { if (d.parent !== focus) this.style.display = "none"; });
                ////.each("end", function(d) { if (d.parent == focus) this.style.display = "none"; });
        }

        function zoomTo(v) {
            var k = diameter / v[2]; view = v;
            node.attr("transform", function(d) { return "translate(" + (d.x - v[0]) * k + "," + (d.y - v[1]) * k + ")"; });
            circle.attr("r", function(d) { return d.r * k; });
        }

        d3.select(self.frameElement).style("height", diameter + "px");
    };
    */

    // Draws a zoomable treemap
    curious.treemap = function(options) {
        var options = options || {};
        var container = "#"+options.container;
        var data = JSON.parse(JSON.stringify(options.data));
        var width = options.width;
        var height = options.height;
        var margin = options.margin;
        var color = options.color || d3.scale.category20();
        var tooltips = options.tooltips || false;
        var size_col = options.size_col;

        function zoom(d) {
            var x = d3.scale.linear().range([0, width]);
            var y = d3.scale.linear().range([0, height]);

            var kx = width / d.dx, ky = height / d.dy;
            x.domain([d.x, d.x + d.dx]);
            y.domain([d.y, d.y + d.dy]);

            var t = svg.selectAll("g.cell")
                .transition()
                .duration(d3.event.altKey ? 7500 : 750)
                .attr("transform", function(d) { return "translate(" + x(d.x) + "," + y(d.y) + ")"; });
            t.select("rect")
                .attr("width", function(d) { return kx * d.dx - 1; })
                .attr("height", function(d) { return ky * d.dy - 1; });

            t.select("text")
                .attr("x", function(d) { return kx * d.dx / 2; })
                .attr("y", function(d) { return ky * d.dy / 2; })
                .style("opacity", function(d) { return kx * d.dx > d.w ? ( ky * d.dy > 15 ? 1 : 0) : 0; });

            node = d;
            d3.event.stopPropagation();
        }

        if (!size_col) console.log("Error: size_col must be specified.");

        var treemap = d3.layout.treemap()
            .round(false)
            .size([width, height])
            .sticky(true)
            .value(function(d) { return d[size_col]; });

        // Create SVG canvas
        var svg = d3.select(container)
        .append("div")
            .style("position", "relative")
            .style("width", width + "px")
            .style("height", height + "px")
            .style("top", margin.top + "px")
            .style("display", "inline-block")
        .append("svg")
            .attr("width", width)
            .attr("height", height)
        .append("g")
            .attr("transform", "translate(.5,.5)");

        node = root = data;

        var nodes = treemap.nodes(root)
            .filter(function(d) { return !d.children; });

        var cell = svg.selectAll(".cell")
            .data(nodes)
        .enter().append("g")
            .filter(function(d) { return d.children ? true : (d[size_col])>0; })
            .attr("class", "cell")
            .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
            .on("click", function(d) { if(tooltips) tip.hide(); return zoom(node == d.parent ? root : d.parent); });

        cell.append("rect")
            .attr("width", function(d) { return d.dx - 1; })
            .attr("height", function(d) { return d.dy - 1; })
            .style("fill", function(d) { return color(d.parent.name); });
            
        cell.append("svg:text")
            .attr("x", function(d) { return d.dx / 2; })
            .attr("y", function(d) { return d.dy / 2; })
            .attr("dy", ".35em")
            .attr("text-anchor", "middle")
            .text(function(d) { return d.name; })
            .style("font-weight", "400")
            .style("fill", function(d) {
                var c = d3.rgb(color(d.parent.name)); 
                var o = Math.round((c.r * 299 + c.g * 587 + c.b * 114) /1000);
                return o>125 ? "#444" : "#eee";
            })
            .style("opacity", function(d) { d.w = this.getComputedTextLength(); return d.dx > d.w ? (d.dy>15 ? 1 : 0) : 0; });

        // If tooltips are enabled...
        if(tooltips) {
            // Create tip object
            var tip = d3.tip()
                .attr('class', 'd3-tip')
                .offset([-10, 0])
                .html(function(d) {
                    return "<p>"+d.parent.name+"</p>/r/"+d.name+": "+d3.format(",d")(d[size_col])+" "+size_col;
                });

            svg.call(tip);

            cell
                .on('mouseenter', tip.show)
                .on('mouseleave', tip.hide);
        }

        d3.select(container).on("click", function() { zoom(root); });

        d3.selectAll("#posts_by_sub_control input").on("change", function change() {
            v = this.value;
            var value = function(d) { return d[v] };
            cell.data(treemap.value(value).nodes().filter(function(d) { return !d.children; }))
                .transition()
                .duration(1500)
                .call(position);

            // If tooltips are enabled...
            if(tooltips) {
                // Create tip object
                var tip = d3.tip()
                    .attr('class', 'd3-tip')
                    .offset([-10, 0])
                    .html(function(d) {
                        return "<p>"+d.parent.name+"</p>/r/"+d.name+": "+d3.format(",d")(d[v])+" "+v;
                    });
                svg.call(tip);
                cell
                    .on('mouseenter', tip.show)
                    .on('mouseleave', tip.hide);
            }
            zoom(root);
        });

        function position() {
            this.style("left", function(d) { return d.x + "px"; })
                .style("top", function(d) { return d.y + "px"; })
                .style("width", function(d) { return Math.max(0, d.dx - 1) + "px"; })
                .style("height", function(d) { return Math.max(0, d.dy - 1) + "px"; });
        }

        function val_array(arr, data,key) {
            if(data.children) {
                data.children.forEach(function(e) {
                    if(e.children) {
                        val_array(arr,e,key);
                    } else {
                        arr.push(+e[key]);
                    }
                });    
            }
        }
    };

    //Draws a sunburst char.
    curious.sunburst = function(options) {
        var options = options || {};
        var container = "#"+options.container;
        var legend_container = "#"+options.legend_container;
        var data = JSON.parse(JSON.stringify(options.data));
        var width = options.width;
        var height = options.height;
        var margin = options.margin;
        var show_percent = options.show_percent || false;
        var color = options.color || d3.scale.category20();
        var b = options.breadcrumb_width || { w: 120, h: 30, s: 3, t: 10 };

        // Fade all but the current sequence, and show it in the breadcrumb trail.
        function mouseover(d) {
            var percentage = (100 * d.value / totalSize).toPrecision(3);
            var percentageString = percentage + "%";
            if (percentage < 0.1) {
                percentageString = "< 0.1%";
            }

            var sequenceArray = getAncestors(d);
            if(show_percent) {
                updateBreadcrumbs(sequenceArray, percentageString);
            } else {
                updateBreadcrumbs(sequenceArray, d.value);
            }

            // Fade all the segments.
            sunburst.selectAll("path")
                .style("opacity", 0.3);

            // Then highlight only those that are an ancestor of the current segment.
            sunburst.selectAll("path")
                .filter(function(node) {
                    return (sequenceArray.indexOf(node) >= 0);
                })
                .style("opacity", 1);
        }

        // Restore everything to full opacity when moving off the visualization.
        function mouseleave(d) {
            // Hide the breadcrumb trail
            d3.select(legend_container+"_trail")
                .style("visibility", "hidden");

            // Deactivate all segments during transition.
            sunburst.selectAll("path").on("mouseover", null);

            // Transition each segment to full opacity and then reactivate it.
            sunburst.selectAll("path")
                .transition()
                .duration(1000)
                .style("opacity", 1)
                .each("end", function() {
                    d3.select(this).on("mouseover", mouseover);
                });
        }

        // Given a node in a partition layout, return an array of all of its ancestor
        // nodes, highest first, but excluding the root.
        function getAncestors(node) {
            var path = [];
            var current = node;
            while (current.parent) {
                path.unshift(current);
                current = current.parent;
            }
            return path;
        }

        function initializeBreadcrumbTrail() {
            // Add the svg area.
            var trail = d3.select(legend_container).append("svg:svg")
                .attr("width", width)
                .attr("height", 50)
                .attr("id", options.legend_container+"_trail");
            // Add the label at the end, for the percentage.
            trail.append("svg:text")
                .attr("id", options.legend_container+"_endlabel")
                .style("fill", "#000");
        }

        // Generate a string that describes the points of a breadcrumb polygon.
        function breadcrumbPoints(d, i) {
            var points = [];
            points.push("0,0");
            points.push(b.w + ",0");
            points.push(b.w + b.t + "," + (b.h / 2));
            points.push(b.w + "," + b.h);
            points.push("0," + b.h);
            if (i > 0) { // Leftmost breadcrumb; don't include 6th vertex.
                points.push(b.t + "," + (b.h / 2));
            }
            return points.join(" ");
        }

        // Update the breadcrumb trail to show the current sequence and percentage.
        function updateBreadcrumbs(nodeArray, value) {
            // Data join; key function combines name and depth (= position in sequence).
            var g = d3.select(legend_container+"_trail")
                .selectAll("g")
                .data(nodeArray, function(d) { return d.name + d.depth; });

            // Add breadcrumb and label for entering nodes.
            var entering = g.enter().append("svg:g");

            entering.append("svg:polygon")
                .attr("points", breadcrumbPoints)
                .style("fill", function(d) { return color(d.name); });

            entering.append("svg:text")
                .attr("x", (b.w + b.t) / 2)
                .attr("y", b.h / 2)
                .attr("dy", "0.35em")
                .attr("text-anchor", "middle")
                .style("font-weight", "500")
                //.style("fill", "#fff")
                .style("fill", function(d) {
                    var c = d3.rgb(color(d.name)); 
                    var o = Math.round((c.r * 299 + c.g * 587 + c.b * 114) /1000);
                    return o>125 ? "#333" : "#eee";
                })
                .text(function(d) { return d.name; });

            // Set position for entering and updating nodes.
            g.attr("transform", function(d, i) {
                return "translate(" + i * (b.w + b.s) + ", 0)";
            });

            // Remove exiting nodes.
            g.exit().remove();

            // Now move and update the percentage at the end.
            d3.select(legend_container+"_trail").select(legend_container+"_endlabel")
                .attr("x", (nodeArray.length + 0.25) * (b.w + b.s))
                .attr("y", b.h / 2)
                .attr("dy", "0.35em")
                .attr("text-anchor", "middle")
                .text(value);

            // Make the breadcrumb trail visible, if it's hidden.
            d3.select(legend_container+"_trail")
                .style("visibility", "");
        }
        
        var radius = Math.min(width, height) / 2;

        // Breadcrumb dimensions: width, height, spacing, width of tip/tail.
        /*
        var b = {
          w: 120, h: 30, s: 3, t: 10
        };
        */

        // Total size of all segments; we set this later, after loading the data.
        var totalSize = 0;

        var sunburst = d3.select(container).append("svg:svg")
            .attr("viewBox", "0 0 " + (width + margin.left + margin.right) + " " + (height + margin.top))
            .attr("preserveAspectRatio", "xMidYMid")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top)
        .append("g")
            .attr("id", container+"_svg")
            .attr("transform", "translate(" + (width+margin.left+margin.right)/2 + "," + (height/2+margin.top) + ")");

        var partition = d3.layout.partition()
            .size([2 * Math.PI, radius * radius])
            .value(function(d) { return d.size; });

        var arc = d3.svg.arc()
            .startAngle(function(d) { return d.x; })
            .endAngle(function(d) { return d.x + d.dx; })
            .innerRadius(function(d) { return Math.sqrt(d.y); })
            .outerRadius(function(d) { return Math.sqrt(d.y + d.dy); });
        
        
        // Basic setup of page elements.
        initializeBreadcrumbTrail();

        // Bounding circle underneath the sunburst, to make it easier to detect
        // when the mouse leaves the parent g.
        sunburst.append("svg:circle")
            .attr("r", radius)
            .style("opacity", 0);

        // For efficiency, filter nodes to keep only those large enough to see.
        var nodes = partition.nodes(data)
            .filter(function(d) {
                return (d.dx > 0.005) && (d.name==="Generic" ? (d.depth==1) : true); // 0.005 radians = 0.29 degrees
            });

        var path = sunburst.data([data]).selectAll("path")
            .data(nodes)
        .enter().append("svg:path")
            .attr("display", function(d) { return d.depth ? null : "none"; })
            .attr("d", arc)
            .attr("fill-rule", "evenodd")
            .style("fill", function(d) { return color(d.name); })
            .style("opacity", 1)
            .on("mouseover", mouseover);

        // Add the mouseleave handler to the bounding circle.
        d3.select(container).on("mouseleave", mouseleave);

        // Get total size of the tree = value of root node from partition.
        totalSize = path.node().__data__.value;
    };

    // Draws a heatmap chart.
    curious.heatmap = function(options) {
        var options = options || {};
        var container = "#"+options.container;
        var data = JSON.parse(JSON.stringify(options.data));
        var width = options.width;
        var height = options.height;
        var margin = options.margin;
        var color = options.color || d3.scale.linear()
            //.domain([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
            .domain([0,15])
            .range(["#ffeeee","#FF0000"]);
            //.range(["#ffeeee", "#FECDCD", "#FEBEBE", "#FEAFAF", "#FEA1A1", "#FE9292", "#FE8383", "#FE7575", 
            //        "#FE6666", "#FE5757", "#FE4949", "#FE3A3A", "#FE2B2B", "#FE1D1D", "#FE0E0E", "#FF0000"]);
        var tooltips = options.tooltips || false;
        var tooltips_msg = options.tooltips_msg || function(){};


        var grid_size = Math.floor(width/data.length);
        var buckets = 10;

        var svg = d3.select(container).append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        var _data = [];
        

        for(var i=0; i<data.length; i++) {
            for(var j=0; j<data[i].length; j++) {
                _data.push({
                    "x": i,
                    "y": j,
                    "value": +data[i][j]
                });
            }
        }

        var heatMap = svg.selectAll(".hour")
            .data(_data)
            .enter().append("rect")
            .attr("x", function(d) { return (d.x + 1) * grid_size; })
            .attr("y", function(d) { return (d.y + 1) * grid_size; })
            .attr("rx", 2)
            .attr("ry", 2)
            .attr("width", grid_size)
            .attr("height", grid_size)
            .style("fill", "#fff");

        
        if(tooltips) {
            // Create tip object
            var tip = d3.tip()
                .attr('class', 'd3-tip')
                .offset([-10, 0])
                .html(tooltips_msg);

            svg.call(tip);

            heatMap
                .on('mouseover', tip.show)
                .on('mouseout', tip.hide);
        }

        heatMap.transition().duration(1000)
            .style("fill", function(d) { return color(d.value); });              
    };

    // Draws a word cloud.
    curious.wordcloud = function(options) {
        var options = options || {};
        var container = "#"+options.container;
        var data = JSON.parse(JSON.stringify(options.data));
        var width = options.width;
        var height = options.height;
        var margin = options.margin;
        var color = options.color || d3.scale.category20();

        if (!data.length) {
            console.log("Error: No data.");
            return;
        }
        min_count = data[data.length-1].size-1;
        max_count = data[0].size;

        var cloud = d3.layout.cloud().size([width, height])
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
            d3.select(container).append("svg")
                .attr("width", width+margin.left+margin.right)
                .attr("height", height)
                .append("g")
                .attr("transform", "translate(" + (width+margin.left+margin.right)/2 +"," + height/2 + ")")
                .selectAll("text")
                .data(words)
            .enter().append("text")
                .style("font-size", function(d) { return d.size + "px"; })
                .style("fill", function(d, i) { return color(i); })
                .attr("text-anchor", "middle")
                .attr("transform", function(d) {
                    return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
                })
                .text(function(d) { return d.text; });

        }
    };

    this.curious = curious;
}();
