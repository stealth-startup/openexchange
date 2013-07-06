/*author: Rex (fdrex1987@gmail.com)*/
function DTable(config) {
//    config = {
//        drawTo:'container',
//        rowNumber: 10,
//        columnWidths:["20%","40%","40%"],
//        headers: ["header1","header2","header3"],
//        columnStyle: ["cssClass1",'',''],
//        initUrl:'/data/url'
//        updateUrl:'/data/url'
//    }
    var thisTable = this;
    $.getJSON(config.initUrl,function(data){
        if (!data || data.length == 0)
            return;
        thisTable.drawTo = config.drawTo;
        thisTable.rowNumber = config.rowNumber ? config.rowNumber : data.length;
        thisTable.lineHeight = $('#'+config.drawTo).height()/(thisTable.rowNumber+1);
        if (thisTable.lineHeight<22){//auto height
            thisTable.lineHeight = 22;
            $("#"+config.drawTo).height(thisTable.lineHeight*(thisTable.rowNumber+1));
        }
        thisTable.columnNumber = data[0].content.length;
        thisTable.headers = config.headers;
        if ('columnWidths' in config)
            thisTable.columnWidths = config.columnWidths;
        else{
            var columnWidths = [];
            var cw = 100/thisTable.columnNumber+'%';
            for (var i=0; i<thisTable.columnNumber; i++)
                columnWidths.push(cw);
            thisTable.columnWidths = columnWidths;
        }
        thisTable.columnStyle = config.columnStyle;
        thisTable.updateUrl = config.updateUrl;
        thisTable.__generateTable(data);
        return this;
    });
}

DTable.prototype.__genHeaders = function(){
    var row = $("<div></div>",{
        style:"margin: 0; width:100%;position: absolute;"
    });
    row.css('height',this.lineHeight).css('top',0).css('font-weight','bold').appendTo(this.row_wrapper);
    var table = $("<table></table>",{style:"border:0; width:100%; height:100%;text-align:center;vertical-align:middle;"});
    var tbody = $("<tbody></tbody>");
    tbody.appendTo(table);

    var tr = $("<tr></tr>");
    tr.appendTo(tbody);
    for(var i=0; i<this.columnNumber;i++){
        $("<td></td>")
            .css('width',this.columnWidths[i])
            .html(this.headers[i])
            .appendTo(tr);
    }
    table.appendTo(row);
}

DTable.prototype.__genRow = function(index,rowData,visibility){
    var row = $("<div></div>",{
        style:"margin: 0; width:100%;position: absolute;"
    });
    row.data('key',rowData.row_key);
    if (!visibility){
        row.css('display','none');
    }
    row.css('height',this.lineHeight).css('top',(index+1)*this.lineHeight).addClass('DTableRow').appendTo(this.row_wrapper);
    var table = $("<table></table>",{style:"border:0; width:100%; height:100%;text-align:center;vertical-align:middle;"});
    table.css('color',rowData.confirmed?'black':'red');
    var tbody = $("<tbody></tbody>");
    tbody.appendTo(table);

    var tr = $("<tr></tr>");
    tr.appendTo(tbody);
    for(var i=0; i<this.columnNumber;i++){
        var td = $("<td></td>")
            .css('width',this.columnWidths[i])
            .html(rowData.content[i])
            .appendTo(tr);
        if (this.columnStyle)
            td.addClass(this.columnStyle[i]);
    }
    table.appendTo(row);
    return row;
}

DTable.prototype.__genHLines = function(){
    for(var i=0; i<this.rowNumber;++i){
        var div = $("<div></div>",{style:"height: 1px; border-top: solid 1px #f0f0f0; position:absolute; width:100%"})
            .css('top',(i+1)*this.lineHeight);
        div.appendTo(this.row_wrapper);
    }
}

//data = [{row_key:1,
//         confirmed:true,
//         content:["hi,there"
//                  ...
//                 ]
//         }...
//       ]
DTable.prototype.__generateTable = function(data){
    this.row_wrapper = $("<div></div>",{
        style:"width: 100%;height: 100%;position: relative;left: 0;top:0;"
    });
    this.row_wrapper.appendTo('#'+this.drawTo);
    this.__genHeaders();
    this.__genHLines();
    for (var i=0; i<data.length; i++){
        this.__genRow(i, data[i],true);
    }
    if (this.updateUrl){
        var thisTable = this;
        setTimeout(function(){ thisTable.__updateData();},2000);
    }
}

DTable.prototype.__updateData = function(){
    var thisTable = this;
    //two steps:
    //1 for those which should disappear, make them disappear
    $.getJSON(this.updateUrl,function(data){
        var new_keys = $.map(data, function(d){ return d.row_key;});
        var deferred = [];
        //thisTable.row_wrapper.children().
        $("#"+thisTable.drawTo+" .DTableRow").each(function(index, element){
            var key = $(element).data('key');
            if ($.inArray(key, new_keys)<0){
                var defferd_obj = new $.Deferred();
                deferred.push(defferd_obj);
                (function(def_obj){
                    $(element).fadeOut(1000,function(){
                        $(this).remove();
                        def_obj.resolve();
                    });
                })(defferd_obj);
            }
        });
        //2 for those which left, change their css properties and make them right position and color
        //for those which newly come, generate and set them right position
        var deferred2 = [];
        $.when.apply($,deferred).done(function(){
            for(var i=0; i<data.length; ++i){
                var defferd2_obj = new $.Deferred();
                deferred2.push(defferd2_obj);

                var old_row = $("#"+thisTable.drawTo+" .DTableRow").filter(function(index){
                    return data[i].row_key == $(this).data('key');
                });
                //if this row exists, change color, do animation
                if (old_row.length>0){
                    old_row = old_row[0];
                    (function(def2_obj){
                        $(old_row).css('color', data[i].confirmed?'black':'red')
                            .animate({
                                top:(i+1)*thisTable.lineHeight
                                },1000,
                                function(){def2_obj.resolve();}
                            );
                    })(defferd2_obj);
                }
                //else create this row, do animation
                else{
                    (function(def2_obj){
                        var new_row = thisTable.__genRow(i,data[i],false);
                        $(new_row).fadeIn(1000,function(){
                            def2_obj.resolve();
                        });
                    })(defferd2_obj);
                }
            }
        });

        $.when.apply($,deferred2).done(function(){
            setTimeout(function(){ thisTable.__updateData();},2000);
        });
    });
}

