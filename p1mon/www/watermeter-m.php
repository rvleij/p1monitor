<?php
include '/p1mon/www/util/page_header.php';
include '/p1mon/www/util/p1mon-util.php';  
include '/p1mon/www/util/page_menu_header_watermeter.php'; 
include '/p1mon/www/util/page_menu.php';
include '/p1mon/www/util/check_display_is_active.php';
include '/p1mon/www/util/weather_info.php';
include '/p1mon/www/util/pageclock.php';
include '/p1mon/www/util/fullscreen.php';

if ( checkDisplayIsActive( 102 ) == false) { return; }
?>
<!doctype html>
<html lang="nl">
<head>
<title>P1monitor watermeter maand</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<link rel="shortcut icon" type="image/x-icon" href="/favicon.ico">
<link type="text/css" rel="stylesheet" href="./css/p1mon.css" />
<link type="text/css" rel="stylesheet" href="./font/roboto/roboto.css"/>

<script defer src="./font/awsome/js/all.js"></script>
<script src="./js/jquery.min.js"></script>
<script src="./js/highstock-link/highstock.js"></script>
<script src="./js/highstock-link/highcharts-more.js"></script>
<script src="./js/hc-global-options.js"></script>
<script src="./js/p1mon-util.js"></script>

<script>
//var seriesOptions   = [];
var recordsLoaded   = 0;
var initloadtimer;
var mins            = 1;  
var secs            = mins * 60;
var currentSeconds  = 0;
var currentMinutes  = 0;
var Gselected       = 0;
var GselectText     = ['6 maanden','1 jaar','2 jaar','5 jaar' ]; // #PARAMETER
var GseriesVisibilty= [true];
var GverbrData      = [];
var GgelvrData      = [];
var GnettoData      = [];
var maxrecords      = 360;

function readJsonApiHistoryMonth( cnt ){ 
    $.getScript( "/api/v1/watermeter/month?limit=" + cnt, function( data, textStatus, jqxhr ) {
      try {
        var jsondata = JSON.parse(data); 
        var item;
        recordsLoaded       = jsondata.length;
        GverbrData.length   = 0;
        
        for (var j = jsondata.length; j > 0; j--){    
            item    = jsondata[ j-1 ];
            item[1] = item[1] * 1000; // highchart likes millisecs.
            GverbrData.push ( [item[1], item[3] ]);
        }  
        updateData();
      } catch(err) {}
   });
}

/* preload */
readJsonApiHistoryMonth( maxrecords );

// change items with the marker #PARAMETER
function createWaterUsageChart() {
    Highcharts.stockChart('WaterUsageChart', {
        chart: {
            style: {
                fontFamily: 'robotomedium'
            },
            backgroundColor: '#ffffff',
            renderTo: 'container',
            type: 'column',
            borderWidth: 0
            },
            plotOptions :{
                series :{
                    showInNavigator: true,
                    events: {
                        legendItemClick: function (event) {
                            console.log(this.index)
                            if  ( this.index === 0 ) {
                                toLocalStorage('watermeter-m-verbr-visible',!this.visible);  // #PARAMETER
                            }
                        }
                    }
                }
            },
            legend: {
                symbolHeight: 12,
                symbolWidth: 12,
                symbolRadius: 3,
                borderRadius: 5,
                borderWidth: 1,
                backgroundColor: '#DCE1E3',
                symbolPadding: 3,
                enabled: true,
                align: 'right',
                verticalAlign: 'top',
                layout: 'horizontal',
                floating: true,
                itemStyle: {
                    color: '#6E797C'
                },
                itemHoverStyle: {
                    color: '#10D0E7'
                },
                itemDistance: 5
            },
            exporting: { enabled: false },
            rangeSelector: {
                inputEnabled: false,
                buttonSpacing: 5, 
                selected : Gselected,
                buttons: [
                {
                    type: 'month',   // #PARAMETER
                    count: 6,        // #PARAMETER
                    text: GselectText[0]
                },{
                    type: 'year',   // #PARAMETER
                    count: 1,       // #PARAMETER
                    text: GselectText[1]
                },{
                    type: 'year',   // #PARAMETER
                    count: 2,       // #PARAMETER
                    text: GselectText[2]
                }, {
                    type: 'year',  // #PARAMETER
                    count: 5,      // #PARAMETER
                    text: GselectText[3]
                }],
                buttonTheme: { 
                    r: 3,
                    fill: '#F5F5F5',
                    stroke: '#DCE1E3',
                    'stroke-width': 1,
                    width: 65,
                    style: {
                        color: '#6E797C',
                        fontWeight: 'normal'
                    },
                states: {
                    hover: {
                        fill: '#F5F5F5',
                        style: {
                            color: '#10D0E7'
                        }
                    },
                    select: {
                        fill: '#DCE1E3',
                        stroke: '#DCE1E3',
                        'stroke-width': 1,
                        style: {
                            color: '#384042',
                            fontWeight: 'normal'
                        }
                    }
                }
                }  
            },
            xAxis: {
            events: {
                setExtremes: function(e) {  	
                    if(typeof(e.rangeSelectorButton)!== 'undefined') {
                        for (var j = 0;  j < GselectText.length; j++){    
                            if ( GselectText[j] == e.rangeSelectorButton.text ) {
                                toLocalStorage('watermeter-m-select-index',j); // PARAMETER
                                break;
                            }
                        }
                    }
                }
            },   
            minTickInterval:       30 * 24 * 3600000,  // PARAMETER
            range:           60  * 30 * 24 * 3600000,  // PARAMETER
            minRange:        6   * 30 * 24 * 3600000,  // PARAMETER
            maxRange:        120 * 30 * 24 * 3600000,  // PARAMETER
            type: 'datetime',
            dateTimeLabelFormats: {
                day: '%a.<br>%d %B<br/>%Y',
                hour: '%a.<br>%H:%M'
            },
            lineColor: '#6E797C',
            lineWidth: 1
            },
            yAxis: {
                gridLineColor: '#6E797C',
                gridLineDashStyle: 'longdash',
                lineWidth: 0,
                offset: 0,
                opposite: false,
                labels: {
                    useHTML: true,
                    format: '{value} L',
                    style: {
                        color: '#6E797C'
                    },
                },
                plotLines: [{
                    value: 0,
                    width: 1,
                    color: '#6E797C'
                }]
            },
            tooltip: {
            useHTML: true,
                style: {
                    padding: 3,
                    color: '#6E797C'
                },
            formatter: function() {
                //var s = '<b>'+ Highcharts.dateFormat('%A, %Y-%m-%d %H:%M-%H:59', this.x) +'</b>';
                var s = '<b>'+ Highcharts.dateFormat('%B, %Y', this.x) +'</b>';

                var d = this.points;
                var verbruikt   = "verborgen";
                var d           = this.points;

                var Pverbruik = 0;
               
                for (var i=0,  tot=d.length; i < tot; i++) {
                    //console.log (d[i].series.userOptions.id);
                    if  ( d[i].series.userOptions.id === 'verbruik') {
                        Pverbruik = d[i].y;
                    }
                }
                
                if ( $('#WaterUsageChart').highcharts().series[0].visible === true ) {
                    verbruikt = Pverbruik.toFixed(1)+" Liter";
                }
                
                s += '<br/><span style="color: #6699ff;">verbruikt:&nbsp;</span>' + verbruikt + " (" + (parseFloat(verbruikt)/1000).toFixed(3) + " m<sup>3</sup>) water";
                return s;
            },
            backgroundColor: '#F5F5F5',
            borderColor: '#DCE1E3',
            crosshairs: [true, true],
            borderWidth: 1
            },  
            navigator: {
                xAxis: {
                    //min: 915145200000, //vrijdag 1 januari 1999 00:00:00 GMT+01:00
                    minTickInterval:       24 * 3600000,  // PARAMETER
                    maxRange:         30 * 24 * 3600000,  // PARAMETER
                    dateTimeLabelFormats: {
                        day: '%d %B'	
                    }    
                },
                enabled: true,
                outlineColor: '#384042',
                outlineWidth: 1,
                handles: {
                    backgroundColor: '#384042',
                    borderColor: '#6E797C'
                },
                series: {
                    color: '#10D0E7'
                }
            },
            series: [ 
            {
                id: 'verbruik',
                visible: GseriesVisibilty[0],
                name: 'Liter verbruikt',
                color: '#6699ff',
                data: GverbrData 
            } 
            ],
            lang: {
                noData: "Geen gegevens beschikbaar."
            },
            noData: {
                style: { 
                    fontFamily: 'robotomedium',   
                    fontWeight: 'bold',     
                    fontSize: '25px',
                    color: '#10D0E7'        
                }
            }        
  });
}

function updateData() {
    //console.log("updateData()");
    var chart = $('#WaterUsageChart').highcharts();
    if( typeof(chart) !== 'undefined') {
        chart.series[0].setData( GverbrData );
        /*
        chart.series[0].update({
        pointStart: GverbrData[0][0],
        data: GverbrData
        }, false);
        chart.redraw();
        */
    }
}

function DataLoop() {
    currentMinutes = Math.floor(secs / 60);
    currentSeconds = secs % 60;
    if(currentSeconds <= 9) { currentSeconds = "0" + currentSeconds; }
    secs--;
    document.getElementById("timerText").innerHTML = zeroPad(currentMinutes,2) + ":" + zeroPad(currentSeconds,2);
    if(secs < 0 ) { 
        mins = 1;  
        secs = mins * 60;
        currentSeconds = 0;
        currentMinutes = 0;
        colorFader("#timerText","#0C7DAD");
        readJsonApiHistoryMonth( maxrecords );
    }
    // make chart only once and when we have data.
    if (recordsLoaded !== 0 &&  $('#WaterUsageChart').highcharts() == null) {
      hideStuff('loading-data');
      createWaterUsageChart();
    }
    setTimeout('DataLoop()',1000);
}

$(function() {
    toLocalStorage('watermeter-menu',window.location.pathname);
    Gselected = parseInt( getLocalStorage('watermeter-m-select-index'), 10 );
    GseriesVisibilty[0] =JSON.parse( getLocalStorage('watermeter-m-verbr-visible') );  // #PARAMETER
    Highcharts.setOptions({
    global: {
        useUTC: false
        }
    });
    secs = 0;
    screenSaver( <?php echo config_read(79);?> ); // to enable screensaver for this screen.
    DataLoop();
});

</script>
</head>
<body>
<div class="top-wrapper">
    <div class="content-wrapper">   
        <?php page_header();?>     
    </div>
</div>

<div class="top-wrapper-2">
    <div class="content-wrapper pad-13">
       <!-- header 2 -->
       <?php pageclock(); ?>
       <?php page_menu_header_watermeter( 2 ); ?>
	   <?php weather_info(); ?>
    </div>
</div>

<div class="mid-section">
    <div class="left-wrapper">
        <?php page_menu(9); ?>
        <div id="timerText" class="pos-8 color-timer"></div>
        <?php fullscreen(); ?>
    </div> 
    <div class="mid-content-2 pad-13">
    <!-- links -->
    	<div class="frame-2-top">
    		<span class="text-2">maanden (liter water)</span>
    	</div>
    	<div class="frame-2-bot"> 
    	<div id="WaterUsageChart" style="width:100%; height:480px;"></div>	
    	</div>
</div>
</div>
<div id="loading-data"><img src="./img/ajax-loader.gif" alt="Even geduld aub." height="15" width="128" /></div>   

</body>
</html>