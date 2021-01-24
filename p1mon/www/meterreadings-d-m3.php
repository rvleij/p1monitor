<?php
include '/p1mon/www/util/page_header.php';
include '/p1mon/www/util/p1mon-util.php';  
include '/p1mon/www/util/page_menu.php';
include '/p1mon/www/util/check_display_is_active.php';
include '/p1mon/www/util/weather_info.php';
include '/p1mon/www/util/pageclock.php';
include '/p1mon/www/util/fullscreen.php';
include '/p1mon/www/util/page_menu_header_meterreadings.php';

if ( checkDisplayIsActive(62) == false) { return; }
?>
<!doctype html>
<html lang="nl">
<head>
<title>P1monitor historie dag meterstanden</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<link rel="shortcut icon" type="image/x-icon" href="/favicon.ico">
<link type="text/css" rel="stylesheet" href="./css/p1mon.css"/>
<link type="text/css" rel="stylesheet" href="./font/roboto/roboto.css"/>

<script defer src="./font/awsome/js/all.js"></script>
<script src="./js/jquery.min.js"></script>
<script src="./js/highstock-link/highstock.js"></script>
<script src="./js/highstock-link/highcharts-more.js"></script>
<script src="./js/hc-global-options.js"></script>
<script src="./js/p1mon-util.js"></script>
<script>
"use strict"; 
// change items with the marker #PARAMETER
var consumptionKwhGas   = [];
var consumptionWater    = [];
var seriesOptions       = [];
var recordsLoaded       = 0;
var initloadtimer;
var Gselected           = 0;
var GselectText         = [ '1 week','1 maand','1 jaar','totaal' ]; // #PARAMETER
var GseriesVisibilty    = [ true,true ];
var mins                = 1;
var secs                = mins * 60;
var currentSeconds      = 0;
var currentMinutes      = 0;


function readJsonApiHistoryDay( cnt ){ 
    $.getScript( "/api/v1/powergas/day", function( data, textStatus, jqxhr ) {
      try {
        var jsondata = JSON.parse(data); 
        var item;
        recordsLoaded = jsondata.length;

        //empty the arrays.
        consumptionKwhGas.length    = 0;
        consumptionWater.length     = 0;

        for (var j = jsondata.length; j > 0; j--){    
            item    = jsondata[ j-1 ];
            item[1] = item[1] * 1000; // highchart likes millisecs.

            consumptionKwhGas.push(   [ item[1], item[8] ] );
            consumptionWater.push(    [ item[1], null ]    );  // the null will be filled by another ajax call.
        } 
        readJsonApiHistoryWaterDay( cnt )
      } catch(err) {
        console.log( err )
      }
   });
}

function readJsonApiHistoryWaterDay( cnt ){ 
    $.getScript( "/api/v1/watermeter/day", function( data, textStatus, jqxhr ) {
      try {
        var jsondata = JSON.parse(data); 

        for( var j=0; j<jsondata.length; j++ ) {
            for ( var n=0; n<consumptionWater.length; n++) {
                if ( (jsondata[j][1] * 1000) == consumptionWater[n][0] ) {
                    consumptionWater[n][1] = jsondata[j][4];
                }
            }
        }
        updateData(); 
      } catch(err) {
        console.log( err )
      }
   });
}

// change items with the marker #PARAMETER
function createMeterReadingsChart() {
  Highcharts.stockChart('meterReadingChart', {
  exporting: { enabled: false },
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
  },
  chart: {
    //ignoreHiddenSeries: false,
    style: {
      fontFamily: 'robotomedium'
    },
    backgroundColor: '#ffffff',
    borderWidth: 0
  },   
  title: {
            margin: 0,
            text: 'placeholder', 
            style: {
                color: '#FFFFFF',
                fontWeight: 'bold',
                fontSize: "10px"
            }
  },
  navigator: {
    xAxis: {
      minTickInterval:  1 * 24 * 3600000, 
      maxRange:        25 * 365 * 24 * 3600000,
      type: 'datetime',
      dateTimeLabelFormats: {
        day: '%a.<br>%d %B<br/>%Y',
        month: '%B<br/>%Y',
        year: '%Y'
      }  
    },  
    enabled: true,
    outlineColor: '#384042',
    outlineWidth: 1,
    handles: {
      backgroundColor: '#384042',
      borderColor: '#6E797C'
    },
    
  },   
  xAxis: {
   type: 'datetime',
   minTickInterval: 1   * 24 * 3600000, 
   range:          5000 * 24 * 3600000,
   minRange:       7  * 24 * 3600000,
   maxRange:       61 * 24 * 3600000,
   dateTimeLabelFormats: {
     day: '%a.<br>%d %b<br/>%Y',
     hour: '%a.<br>%H:%M',
     year: '%Y'
   },
   lineColor: '#6E797C',
   lineWidth: 1, 
   events: {
        setExtremes: function(e) {
        if(typeof(e.rangeSelectorButton)!== 'undefined') {
         for (var j = 0;  j < GselectText.length; j++){    
           if ( GselectText[j] == e.rangeSelectorButton.text ) {
             toLocalStorage('select-meterreadings-d-m3-index',j); // #PARAMETER
             break;
           }
         }
       }
     }
   },   
  },
  yAxis: [
    { // gas axis & water
        showEmpty: false,
        tickAmount: 7,
        opposite: false,
        offset: null,
        labels: {
            useHTML: false,
            format: '{value} m<sup>3</sup>',
            style: {
                color: '#507ABF',
            },
        },
        title: {
        text: null, 
        },
    }
    
    
  ],
  tooltip: {
       useHTML: false,
        style: {
            padding: 3,
            color: '#6E797C'
        },
      formatter: function() {
        
        var s = '<b>'+ Highcharts.dateFormat('%A, %Y-%m-%d', this.x) +'</b>';
        var d = this.points;
           
        for (var i=0,  tot=d.length; i < tot; i++) {

                if ( d[i].series.userOptions.name === 'gas verbruik' ) {
                    s += '<br/><span style="color:#507ABF">Gas verbruik: </span>' + d[i].y.toFixed(3) + " m<sup>3</sup>";
                    //console.log( d[i].y )
                }    
                if ( d[i].series.userOptions.name === 'water verbruik' ) {
                    s += '<br/><span style="color:#6699FF">Water verbruik: </span>' + d[i].y.toFixed(3) + " m<sup>3</sup>";
                    //console.log( d[i].y )
                }  
        }
        //console.log (s)
        return s;
      },
      backgroundColor: '#F5F5F5',
      borderColor: '#DCE1E3',
      crosshairs: [true, true],
      borderWidth: 1
    },
    rangeSelector: { // #PARAMETER
      inputEnabled: false,
       buttonSpacing: 5, 
       selected : Gselected,
       buttons: [{
        type: 'day',
        count: 7,
        text: GselectText[0]
       },{
         type: 'month',
         count: 1,
         text: GselectText[1]
       },{
        type: 'year',
        count: 1,
        text: GselectText[2]
       }, {
        type: 'all',
        //count: 3,
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
      floating: true,
      itemStyle: {
        color: '#6E797C'
      },
      itemHoverStyle: {
        color: '#10D0E7'
      },
      itemDistance: 5
    },
    series: [ 
    {
      yAxis: 0,
      visible: GseriesVisibilty[0],
      showInNavigator: true,
      name: 'gas verbruik',
      type: 'spline',
      color: '#507ABF',
      data: consumptionKwhGas,
      zIndex: 0,
    },
    {
      yAxis: 0,
      visible: GseriesVisibilty[1],
      showInNavigator: true,
      name: 'water verbruik',
      type: 'spline',
      color: '#6699FF',
      data: consumptionWater,
    },
    
    ],
    plotOptions: {
      series: {
        events: {
          legendItemClick: function () {
            //console.log('legendItemClick index='+this.index);
            if ( this.index === 0 ) {
              toLocalStorage('meterreadings-d-consumptionKwhGas',!this.visible); // #PARAMETER
            }
            if ( this.index === 1 ) {
              toLocalStorage('meterreadings-d-consumptionWater',!this.visible); // #PARAMETER
            }
          }
        }
      }
    },
  });
  
}

function updateData() {
    if (recordsLoaded !== 0 ) {
      hideStuff('loading-data');
    }
    // console.log("updateData()");
    var chart = $('#meterReadingChart').highcharts();

    if( typeof(chart) !== 'undefined') {
        chart.series[0].setData( consumptionKwhGas );
        chart.series[1].setData( consumptionWater );
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
        readJsonApiHistoryDay();
    }
    setTimeout('DataLoop()',1000);
}

$(function() {
  toLocalStorage('meterreadings-menu',window.location.pathname);
  GseriesVisibilty[6] = JSON.parse(getLocalStorage('meterreadings-d-consumptionKwhGas')); // #PARAMETER
  GseriesVisibilty[7] = JSON.parse(getLocalStorage('meterreadings-d-consumptionWater')); // #PARAMETER
  Gselected = parseInt(getLocalStorage('select-meterreadings-d-m3-index'),10); // #PARAMETER

  Highcharts.setOptions({
   global: {
    useUTC: false
    }
  });
  screenSaver( <?php echo config_read(79);?> ); // to enable screensaver for this screen.
  secs = 0;
  createMeterReadingsChart();
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
        <?php page_menu_header_meterreadings( 1 ) ?>
        <?php weather_info(); ?>
    </div>
</div>

<div class="mid-section">
    <div class="left-wrapper">
        <?php page_menu( 8 ); ?>
        <div id="timerText" class="pos-8 color-timer"></div>
        <?php fullscreen(); ?>
    </div> 
    <div class="mid-content-2 pad-13">
    <!-- links -->
        <div class="frame-2-top">
            <span class="text-2">meterstanden per dag</span>
        </div>
        <div class="frame-2-bot"> 
        <div id="meterReadingChart" style="width:100%; height:480px;"></div>    
        </div>
</div>
</div>
<div id="loading-data"><img src="./img/ajax-loader.gif" alt="Even geduld aub." height="15" width="128" /></div>   

</body>
</html>