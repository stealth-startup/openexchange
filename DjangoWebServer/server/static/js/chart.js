function fit_chart_into_container(container_id, chart){
    chart.setSize($('#'+container_id).width(),$('#'+container_id).height());
}

function SCChart_auto_update(chart, data_source_url){
    $.ajax(
     {
        url:data_source_url,
        dataType:'json',
        success:function(data){
            chart.series[0].setData(data);
            setTimeout(function(){
                SCChart_auto_update(chart,data_source_url);
            }, 120000);  // 120 seconds is more than enough since the data changes every 10 minutes in average
        }
    });
}

function price_chart(container_id,init_data,data_source_url,title,auto_refresh){
    var chart = new Highcharts.Chart({
        chart: {
            renderTo: container_id,
            events:{
                load: function(){
                    if (auto_refresh){
                        SCChart_auto_update(this,data_source_url);
                    }
                }
            }
        },
        credits:{
            enabled:false
        },
        title: {
            text: title
        },
        xAxis:{
            type:'datetime',
            title:{
                text:null
            }
        },
        yAxis:{
            title:{
                text:'Price'
            }
        },
        series: [{
            name: 'Price',
            data:init_data,
            marker : {
                enabled : true,
                radius : 3
            },
            shadow : true,
            tooltip : {
                valueDecimals : 4
            }
        }]
    });
    fit_chart_into_container(container_id,chart);
}

function price_stock_chart(container_id,init_data,data_source_url,title,auto_refresh){
    var chart = new Highcharts.StockChart({
        chart: {
            renderTo: container_id,
            events:{
                load: function(){
                    if (auto_refresh){
                        SCChart_auto_update(this,data_source_url);
                    }
                }
            }
        },
        credits:{
            enabled:false
        },
        rangeSelector: {
            selected: 1
        },
        title: {
            text: title
        },
        series: [{
            name: 'Price',
            data: init_data,
            marker : {
                enabled : true,
                radius : 3
            },
            shadow : true,
            tooltip : {
                valueDecimals : 4
            }
        }]
    });
    fit_chart_into_container(container_id,chart);
}

function get_stock_price_volume_value(data){
    var price = [],
        volume = [],
        dataLength = data.length;

    for (i = 0; i < dataLength; i++) {
        price.push([
            data[i][0], // timestamp
            data[i][1] // price
        ]);

        volume.push([
            data[i][0], // timestamp
            data[i][2]  //volume
        ])
    }
    return {
        'price':price,
        'volume':volume
    };
}

function PVSChart_auto_update(chart,data_source_url){
    $.ajax(
     {
        url:data_source_url,
        dataType:'json',
        success:function(data){
            var new_v = get_stock_price_volume_value(data);
            chart.series[0].setData(new_v['price']);
            chart.series[1].setData(new_v['volume']);
            setTimeout(function(){
                PVSChart_auto_update(chart,data_source_url);
            },120000);  //120 seconds is more than enough
        }
    });
}

function price_volume_stock_chart(container_id,init_data,data_source_url,title,auto_refresh){
    var v = get_stock_price_volume_value(init_data),
        price = v['price'],
        volume = v['volume'];

    // set the allowed units for data grouping
    var groupingUnits = [[
        'week',                         // unit name
        [1]                             // allowed multiples
    ], [
        'month',
        [1, 2, 3, 4, 6]
    ]];

    var available_height = $('#'+container_id).height()-70;//the bottom bar is about 70px height
    // create the chart
    var chart = new Highcharts.StockChart({
        chart: {
            renderTo: container_id,
            alignTicks: false,
            events:{
                load: function(){
                    if (auto_refresh){
                        PVSChart_auto_update(this,data_source_url);
                    }
                }
            }
        },
        credits:{
            enabled:false
        },
        rangeSelector: {
            selected: 1
        },

        title: {
            text: title
        },

        yAxis: [{
            title: {
                text: 'Price'
            },
            height: available_height*0.56,
            lineWidth: 2
        }, {
            title: {
                text: 'Volume'
            },
            top: available_height*0.66,
            height: available_height*0.24,
            offset: 0,
            lineWidth: 2
        }],

        series: [{
            name: 'Price',
            data: price,
            marker : {
                enabled : true,
                radius : 3
            },
            shadow : true,
            tooltip : {
                valueDecimals : 4
            }
        }, {
            type: 'column',
            name: 'Volume',
            data: volume,
            yAxis: 1,
            dataGrouping: {
                units: groupingUnits
            }
        }]
    });

    fit_chart_into_container(container_id,chart);
}

//chart_type: stock-price, stock-price-volume, chart-price
function draw_chart(container_id, data_source_url, title, chart_type, auto_refresh){
    $.ajax(
        {
        url:data_source_url,
        dataType:'json',
        success:function(data){
            if (chart_type == "stock-price-volume"){
                price_volume_stock_chart(container_id,data,data_source_url,title,auto_refresh);
            }
            else if (chart_type == "stock-price"){
                price_stock_chart(container_id,data,data_source_url,title,auto_refresh);
            }
            else if (chart_type == "chart-price"){
                price_chart(container_id,data,data_source_url,title,auto_refresh);
            }
        }
    })
}