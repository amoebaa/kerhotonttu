

function loadData() {
    d3.csv("data.csv", function(error, data) {
        var parseDate = d3.time.format("%M-%H-%d-%m-%y").parse;
        data.forEach(function(d) {
            d.aika = parseDate(d.aika);
            d.lampo = +d.lampo;
            d.ovi = +d.ovi;
            d.valo = +d.valo;
        });
        drawStuff(data);
    });
}


function drawStuff(data) {
    doordiv = d3.select("#doorChart");
    lightdiv = d3.select("#lightChart");
    tempdiv = d3.select("#tempChart");
    
    
    margin = {top: 15, bottom: 20, left: 50, right: 15};
    size = {width: 500, height: 200};
    
    doordata = {minvalue: 0, maxvalue: 1.5, values: []};
    tempdata = {minvalue: 0, maxvalue: 30, values: []};
    lightdata = {minvalue: 0, maxvalue: 1.5, values: []};
    
    for (var i = 0; i < data.length; i++) {
        doordata.values.push({time: data[i].aika, data: data[i].ovi});
        tempdata.values.push({time: data[i].aika, data: data[i].lampo});
        lightdata.values.push({time: data[i].aika, data: data[i].valo});
    }
    tempchart = lineChart(tempdiv, size, margin, "tempchart");    
    doorchart = lineChart(doordiv, size, margin, "doorchart");
    lightchart = lineChart(lightdiv, size, margin, "lightchart");
    doorchart.drawChart(doordata);
    tempchart.drawChart(tempdata);
    lightchart.drawChart(lightdata);
}