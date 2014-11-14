

function lineChart (div, size, margin, id) {

var that = {};
that.size = {width: size.width, height:size.height};
that.div = div;
that.margin = {top: margin.top, bottom: margin.bottom, left: margin.left, right: margin.right};
that.id = id;

that.drawChart = function(data) {

   that.svg = that.div.append("svg")
      .attr("width", that.size.width)
      .attr("height", that.size.height);
    
   //width and height are size without marginals, chart.size with them
   that.width = that.size.width - that.margin.left - that.margin.right;
   that.height = that.size.height - that.margin.top - that.margin.bottom;
   
   var x = d3.time.scale()
      .range([0, that.width]); 
   
   var y = d3.scale.linear()
      .range([that.height, 0]); 
      
   //set axis domains
   y.domain([data.minvalue, data.maxvalue]);
   x.domain(d3.extent(data.values, function(d) {return d.time;}));
   
   that.svg_inner = that.svg.append("svg")
      .attr("width", that.width)
      .attr("x", that.margin.left)
      .attr("y", that.margin.top)
      .attr("height", that.height)
         
   that.svg_inner.append("rect")
      .attr("width", that.width)
      .attr("height", that.height)
      .attr("x", 0)
      .attr("y", 0)
      .style("opacity", 0);

   var yAxis = d3.svg.axis()
      .scale(y)
      .orient("left");
      
   var xAxis = d3.svg.axis()
      .scale(x)
      .orient("bottom")
      .ticks(6);

   //add y-axis to outer svg element
   that.svg.append("g")
      .attr("class", "x axis")
      .attr("transform", "translate(" + that.margin.left + "," + (that.height + that.margin.top) + ")")
      .call(xAxis);
   if (that.id === "tempchart") {
      that.svg.append("g")
         .attr("class", "y axis")
         .call(yAxis)
         .attr("transform", "translate("  + (that.margin.left) + ", " + that.margin.top + ")")
        .append("text")
         .attr("transform", "rotate(-90)")
         .attr("y", -6)
         .attr("dy", ".71em");   
   }
   else if (that.id === "lightchart") {
      that.svg.append("text")
         .attr("x", 5)
         .attr("y", that.size.height - that.margin.bottom)
         //.attr("transform", "rotate(-90)")
         .text("pois");

      that.svg.append("text")
         .attr("x", 5)
         .attr("y", that.height / 3 + that.margin.top)
         //.attr("transform", "rotate(-90)")
         .text("päällä");  
   }
   else  {
      that.svg.append("text")
         .attr("x", 5)
         .attr("y", that.size.height - that.margin.bottom)
         //.attr("transform", "rotate(-90)")
         .text("kiinni");

      that.svg.append("text")
         .attr("x", 5)
         .attr("y", that.height / 3 + that.margin.top)
         //.attr("transform", "rotate(-90)")
         .text("auki");  
   }
      
   //define line for
   var line = d3.svg.line()
      .x(function(d) { return x(d.time); })
      .y(function(d) { return y(d.data); });
   
   //make line for each dataset
   that.svg_inner.append("path")
      .datum(data.values)
      .attr("class", "line")
      .attr("d", line)
      .style("stroke", function(d) { return "steelblue"; })
      .style("fill", "none")
      .style("stroke-width", "1.5");
};

return that;
}
