<?php
include_once '/p1mon/www/util/page_header.php';
include_once '/p1mon/www/util/p1mon-util.php';  
include_once '/p1mon/www/util/page_menu.php';
include_once '/p1mon/www/util/page_menu_header_heating.php';
include_once '/p1mon/www/util/check_display_is_active.php';
include_once '/p1mon/www/util/weather_info.php';
include_once '/p1mon/www/util/pageclock.php';
include_once '/p1mon/www/util/fullscreen.php';

if ( checkDisplayIsActive(46) == false) { return; }
?>
<!doctype html>
<html lang="nl">
<head>
<title>P1monitor verwarming dag</title>
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
"use strict"; 

var GrangeIn        = [];
var GrangeInAvg     = [];
var GrangeOut       = [];
var GrangeOutAvg    = [];

var seriesOptions   = [];
var recordsLoaded   = 0;
var initloadtimer;
var Gselected       = 0;
var GselectText     = ['1 week','14 dagen','1 maand','2 maanden']; // #PARAMETER
var GseriesVisibilty= [true,true,true,true];
var GserieNames     = ["IN","IN(GEM.)","UIT","UIT(GEM.)"]
var mins            = 1;
var secs            = mins * 60;
var currentSeconds  = 0;
var currentMinutes  = 0;
var maxrecords      = 366; // number of records to read
var ui_in_label     = "<?php echo config_read( 121 ); ?>"; 
var ui_uit_label    = "<?php echo config_read( 122 ); ?>";

function setLabels() {
    if ( ui_in_label.length > 0 ) {
        GserieNames[0] = ui_in_label;
        GserieNames[1] = ui_in_label +"(GEM.)";
    }
    if ( ui_uit_label.length > 0 ) {
        GserieNames[2] = ui_uit_label;
        GserieNames[3] = ui_uit_label +"(GEM.)";
    }
}

function readJsonIndoorTemperatureDay( cnt ){ 
    $.getScript( "./api/v1/indoor/temperature/day?limit=" + cnt , function( data, textStatus, jqxhr ) {
      try {
        var jsondata = JSON.parse(data); 
        var item;
        recordsLoaded = jsondata.length;
        GrangeIn.length = 0;
        GrangeOut.length= 0;
        GrangeInAvg.length=0;
        GrangeOutAvg.length=0;
        for (var j = jsondata.length; j > 0; j--){    
          item=jsondata[j-1];
          item[1] = item[1]*1000; // highcharts likes millisecs.
          GrangeIn.push(    [item[1], item[4], item[6]  ]); //in max, out min
          GrangeOut.push(   [item[1], item[8], item[10] ]); //in max, out min
          GrangeInAvg.push( [item[1], item[5]           ]); //in avg
          GrangeOutAvg.push([item[1], item[9]           ]); //out avg
        } 
        updateData();
      } catch(err) {}
   });
}

// change items with the marker #PARAMETER
function createChart() {
  Highcharts.stockChart('tempChart', {
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
    style: {
      fontFamily: 'robotomedium'
    },
    backgroundColor: '#ffffff',
    borderWidth: 0
  },   
  title: {
   text: null
  },  
  navigator: {
    xAxis: {
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
    series:[ 
      {
        color: '#507ABF'
      }, 
      {
        color: '#384042'
      }
    ]
  },   
  xAxis: {
    type: 'datetime', 
    minTickInterval: 24 *  3600000, 
    dateTimeLabelFormats: {
        day: '%a.<br>%d %B<br/>%Y',
        hour: '%a.<br>%H:%M'
    },
    lineColor: '#6E797C',
    lineWidth: 1, 
    events: {
     setExtremes: function(e) {      
       if(typeof(e.rangeSelectorButton)!== 'undefined') {
         for (var j = 0;  j < GselectText.length; j++){    
           if ( GselectText[j] == e.rangeSelectorButton.text ) {
             toLocalStorage('verwarming-d-select-temperatuur-index',j); // #PARAMETER
             break;
           }
         }
       }
     }
   },    
  },
  yAxis: [
    { // temp axis
    tickAmount: 7,
    opposite: false,
    gridLineDashStyle: 'longdash',
    gridLineColor: '#6E797C',
    gridLineWidth: 1,
    labels: {
      format: '{value}°C',
        style: {
          color: '#384042'
        }
     },
     title: {
       text: null, 
     },
  }],
  tooltip: {
      useHTML: true,
      style: {
        padding: 3,
        color: '#6E797C'
      },
      formatter: function() {
        
        var s = '<b>'+ Highcharts.dateFormat('%A, %Y-%m-%d', this.x) +'</b>'; //parameter
        var d = this.points;
        
        var in_temp_min  = 'verborgen';
        var in_temp_max  = 'verborgen';
        var in_temp_avg  = 'verborgen';
        var out_temp_min = 'verborgen';
        var out_temp_max = 'verborgen';
        var out_temp_avg = 'verborgen';
        var in_header    = '';
        var out_header   = '';
        var delta_header = '';

        var max_temp_color = '#FF0000';
        var min_temp_color = '#0088FF';

        for (var i = 0; i < d.length; i++) { 

          if (d[i].series.name == GserieNames[0] && d[i].series.visible == true) {
            in_temp_max = d[i].point.high;
            in_temp_min = d[i].point.low;
            if ( in_header == '') {
              in_header = "<br/><br/><span>Temperatuur " + GserieNames[0] + ":</span>"
              s += in_header;
            }
            s += '<br/><span style="color: #FF0000">Maximum: </span>'+in_temp_max.toFixed(1)+"°C";;
            s += '<br/><span style="color: #FF6666">Minimum: </span>'+in_temp_min.toFixed(1)+"°C";
          }

           if (d[i].series.name == GserieNames[1] && d[i].series.visible == true) {
            in_temp_avg = d[i].point.y;
            if ( in_header == '') {
              in_header = "<br/><br/><span>Temperatuur " + GserieNames[1] + ":</span>"
              s += in_header;
            }
            s += '<br/><span style="color: #ff3333">Gemiddelde: </span>'+in_temp_avg.toFixed(1)+"°C";
          }

          if (d[i].series.name == GserieNames[2] && d[i].series.visible == true) {
            out_temp_max = d[i].point.high;
            out_temp_min = d[i].point.low;
            if ( out_header == '') {
              out_header = "<br/><br/><span>Temperatuur " + GserieNames[2] + ":</span>"
              s += out_header;
            }
            s += '<br/><span style="color: #0000FF">Maximum: </span>'+out_temp_max.toFixed(1)+"°C";
            s += '<br/><span style="color: #0088FF">Minimum: </span>'+out_temp_min.toFixed(1)+"°C";
          }

          if (d[i].series.name == GserieNames[3] && d[i].series.visible == true) {
            out_temp_avg = d[i].point.y;
            if ( out_header == '') {
              out_header = "<br/><br/><span>Temperatuur " + GserieNames[3] + ":</span>"
              s += out_header;
            }
            s += '<br/><span style="color: #3333ff">Gemiddelde: </span>'+out_temp_avg.toFixed(1)+"°C";
          }
        }

        if (in_temp_avg != 'verborgen' && out_temp_avg != 'verborgen') {
          if ( delta_header == '') {
            delta_header= "<br/><br/><span>Verschil temperatuur:</span>"
            s += delta_header;
          }
          s += '<br/><span style="color: #3333ff">Gemiddelde ' + GserieNames[0] + ' - ' + GserieNames[2] + ': </span>'+Math.abs(in_temp_avg - out_temp_avg).toFixed(1)+"°C";
        }

        if (in_temp_max != 'verborgen' && out_temp_min != 'verborgen') {
          if ( delta_header == '') {
            delta_header = "<br/><br/><span>Verschil temperatuur:</span>"
            s += delta_header;
          }
          s += '<br/><span style="color: #3333ff">Max ' + GserieNames[0] + ' - ' + GserieNames[2] + ': </span>'+Math.abs(in_temp_max - out_temp_min).toFixed(1)+"°C";
        }
        return s;
      },
      backgroundColor: '#F5F5F5',
      borderColor: '#DCE1E3',
      crosshairs: [true, true],
      borderWidth: 1
    },
    rangeSelector: {
      inputEnabled: false,
       buttonSpacing: 5, 
       selected : Gselected,
       buttons: [{
        type: 'day',
        count: 7,
        text: GselectText[0]
       },{
         type: 'day',
         count: 14,
         text: GselectText[1]
       },{
        type: 'month',
        count: 1,
        text: GselectText[2]
       }, {
        type: 'month',
        count: 2,
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
    series: [{
      showInNavigator: true,
      yAxis: 0,
      dashStyle: 'ShortDot',
      visible: GseriesVisibilty[0],
      name: GserieNames[0],
      data: GrangeIn,
      type: 'areasplinerange',
      lineWidth: 1,
      color: '#FF0000',
      negativeColor: '#0088FF',
      fillOpacity: 0.3,
      zIndex: 1,
      marker: {
        fillColor: 'white',
        lineWidth: 1,
        lineColor: '#ff0000'
        } 
      },
      {
      visible: GseriesVisibilty[1],
      showInNavigator: true,
      name: GserieNames[1],
      data: GrangeInAvg,
      type: 'spline',
      zIndex: 2,
      color: '#FF0000',
      lineWidth: 1,
      marker: {
        fillColor: 'white',
        lineWidth: 1,
        lineColor: '#384042'
        }
      },
      {
      dashStyle: 'ShortDot',
      visible: GseriesVisibilty[2],
      showInNavigator: true,
      name: GserieNames[2],
      data: GrangeOut,
      type: 'areasplinerange',
      lineWidth: 1,
      color: '#0000FF',
      negativeColor: '#0088FF',
      fillOpacity: 0.3,
      zIndex: 3,
      marker: {
        fillColor: 'white',
        lineWidth: 1,
        lineColor: '#ff0000'
        }
      },
      {
      visible: GseriesVisibilty[3],
      showInNavigator: true,
      name: GserieNames[3],
      data: GrangeOutAvg,
      type: 'spline',
      zIndex: 3,
      color: '#0000FF',
      lineWidth: 1,
      marker: {
        fillColor: 'white',
        lineWidth: 1,
        lineColor: '#384042'
      } 
    }
    ],
    plotOptions: {
      series: {
        showInNavigator: true,
        events: {
          legendItemClick: function () {
            // console.log('legendItemClick index='+this.index);
            if ( this.index === 0 ) {
              toLocalStorage('verwarming-d-in-visible',!this.visible); // #PARAMETER
            }
            if ( this.index === 1 ) {
              toLocalStorage('verwarming-d-in-gem-visible',!this.visible); // #PARAMETER
            }
            if ( this.index === 2 ) {
              toLocalStorage('verwarming-d-uit-visible',!this.visible); // #PARAMETER
            }
            if ( this.index === 3 ) {
              toLocalStorage('verwarming-d-uit-gem-visible',!this.visible); // #PARAMETER
            }
          }
        }
      }  
    },
  });
}

function updateData() {
    // console.log("updateData()");
    var chart = $('#tempChart').highcharts();
    if( typeof(chart) !== 'undefined') {
        chart.series[0].setData( GrangeIn )
        chart.series[1].setData( GrangeInAvg )
        chart.series[2].setData( GrangeOut )
        chart.series[3].setData( GrangeOutAvg )
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
        readJsonIndoorTemperatureDay( maxrecords );
    }
    
    if (recordsLoaded !== 0 && $('#tempChart').highcharts() == null ) {
      hideStuff('loading-data');
      createChart();
      updateData();
    }
    setTimeout('DataLoop()',1000);
}

$(function() {
    setLabels();
    toLocalStorage('verwarming-menu',window.location.pathname);
    GseriesVisibilty[0] = JSON.parse(getLocalStorage('verwarming-d-in-visible'));
    GseriesVisibilty[1] = JSON.parse(getLocalStorage('verwarming-d-in-gem-visible'));
    GseriesVisibilty[2] = JSON.parse(getLocalStorage('verwarming-d-uit-visible'));
    GseriesVisibilty[3] = JSON.parse(getLocalStorage('verwarming-d-uit-gem-visible'));
    Gselected = parseInt(getLocalStorage('verwarming-d-select-temperatuur-index'),10);
    Highcharts.setOptions({
        global: {
        useUTC: false
        }
    });
    screenSaver( <?php echo config_read(79);?> ); // to enable screensaver for this screen.
    secs = 0;
    DataLoop();
});

</script>
</head>
<body>

<?php page_header();?>

<div class="top-wrapper-2">
    <div class="content-wrapper pad-13">
       <!-- header 2 -->
        <?php pageclock(); ?>
        <?php page_menu_header_heating(3); ?>  <!-- parameter -->
        <?php weather_info(); ?>
    </div>
</div>

<div class="mid-section">
    <div class="left-wrapper">
        <?php page_menu(7); ?>
        <div id="timerText" class="pos-8 color-timer"></div>
        <?php fullscreen(); ?>
    </div> 
    <div class="mid-content-2 pad-13">
    <!-- links -->
        <div class="frame-2-top">
            <span class="text-2">dagen verwarming temperatuur in °C</span>
        </div>
        <div class="frame-2-bot"> 
        <div id="tempChart" style="width:100%; height:480px;"></div>    
        </div>
</div>
</div>
<div id="loading-data"><img src="./img/ajax-loader.gif" alt="Even geduld aub." height="15" width="128" /></div>   

</body>
</html>