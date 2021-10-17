<?php
include_once '/p1mon/www/util/page_header.php';
include_once '/p1mon/www/util/p1mon-util.php';  
include_once '/p1mon/www/util/page_menu.php';
include_once '/p1mon/www/util/page_menu_header_gas.php';
include_once '/p1mon/www/util/check_display_is_active.php';
include_once '/p1mon/www/util/weather_info.php';
include_once '/p1mon/www/util/pageclock.php';
include_once '/p1mon/www/util/fullscreen.php';

if ( checkDisplayIsActive(20) == false) { return; }
?>
<!doctype html>
<html lang="nl">
<head>
<meta name="robots" content="noindex">
<title>P1monitor historie dag gas</title>
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
var GverbrData      = [];
var Granges         = [];
var Gaverages       = [];

var seriesOptions   = [];
var recordsLoaded   = 0;
var initloadtimer;
var Gselected       = 0;
var GselectText     = ['1 week','14 dagen','1 maand','2 maanden']; // #PARAMETER
var GseriesVisibilty= [true,true];
var mins            = 1;
var secs            = mins * 60;
var currentSeconds  = 0;
var currentMinutes  = 0;
var maxrecords      = 366; // number of records to read 



function readJsonApiHistoryDay( cnt ){ 
    $.getScript( "/api/v1/powergas/day?limit=" + cnt, function( data, textStatus, jqxhr ) {
      try {
        var jsondata = JSON.parse(data); 
        var item;
        recordsLoaded = jsondata.length;

        //empty the array.
        GverbrData.length = 0; 
        Granges.length    = 0;
        Gaverages.length  = 0;

        for (var j = jsondata.length; j > 0; j--){    
            item    = jsondata[ j-1 ];
            item[1] = item[1] * 1000; // highchart likes millisecs.
            GverbrData.push( [item[1], item[9] ]   );
            //GverbrData.push( [item[1], 10 ]   );
            Granges.push   ( [item[1], null, null ] );
            Gaverages.push ( [item[1], null ]       );
        } 

        readJsonApiWeatherHistoryDay( cnt ) 
      } catch(err) {
        console.log( err )
      }
   });
}

function readJsonApiWeatherHistoryDay( cnt ){ 
    $.getScript( "/api/v1/weather/day?limit=" + cnt, function( data, textStatus, jqxhr ) {
      try {
        var jsondata = JSON.parse(data); 
        //var t0 = performance.now();
        for (var j = 0; j < jsondata.length; j++){    
            var item = jsondata[ j ];
            for ( var k=0 ; k < GverbrData.length; k++ ) {
                //console.log( "timestamp gaswaarde=" + GverbrData[k][0] + " gaswaarde=" + GverbrData[0][1] );
                //console.log( "k=" + k + " item[1]=" + item[1] * 1000  );
                if ( GverbrData[k][0] == item[1] * 1000 ) {
                    //console.log( "timestamp komt overeen, range waarde =" + item[4] + " k=" + k);
                    Granges[k][1]   = item[4]
                    Granges[k][2]   = item[6]
                    Gaverages[k][1] = item[5]
                    break;
                    
                }
                
            }
        }  
        //var t1 = performance.now();
        //console.log("Call to process took " + (t1 - t0) + " milliseconds.")
        updateData();
      } catch(err) {
        console.log( err )
      }
   });
}

// change items with the marker #PARAMETER
function createGasChart() {
  Highcharts.stockChart('GasChart', {
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
      //min: 915145200000, //vrijdag 1 januari 1999 00:00:00 GMT+01:00
      minTickInterval:  1 * 24 * 3600000, 
      maxRange:       365 * 24 * 3600000,
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
   minTickInterval: 1 * 24 * 3600000, 
   range:          31 * 24 * 3600000,
   //minRange:       7  * 24 * 3600000,
   //maxRange:       61 * 24 * 3600000,
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
             toLocalStorage('stat-d-select-gas-index',j); // #PARAMETER
             break;
           }
         }
       }
     }
   },   
  },
  
  yAxis: [
  { // gas axis
     tickAmount: 7,
     offset: 50,
     labels: {
       useHTML: true,
       //format: '{value} m<sup>3</sup>',
       format: '{value} m&#179;',
         style: {
           color: '#507ABF'
         },
       }
    },
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
        
        //var s = '<b>'+ Highcharts.dateFormat('%A, %Y-%m-%d %H:%M-%H:59', this.x) +'</b>';
        var s = '<b>'+ Highcharts.dateFormat('%A, %Y-%m-%d', this.x) +'</b>';
        var d = this.points;
        
        // find timestamp and add data points
        for (var i=0,  tot=GverbrData.length; i < tot; i++) {
            if ( GverbrData[i][0] == d[0].key ) { //found time and dataset
                var var_verbruikt_gas   = GverbrData[i][1];
                var var_min_temp        = Granges[i][1];
                var var_max_temp        = Granges[i][2];
                var var_avg_temp        = Gaverages[i][1]
                /*
                console.log ( GverbrData[i][1] )
                console.log ( Granges[i][1]    )
                console.log ( Granges[i][2]    )
                console.log ( Gaverages[i][1]  )
                */
                break;
            }
        }
        
        var verbruikt_gas="verborgen";
        if ( $('#GasChart').highcharts().series[0].visible === true ){ // Gas
            verbruikt_gas = var_verbruikt_gas.toFixed(3)+" m<sup>3</sup>";
        }
        s += '<br/><span style="color: #507ABF">gas verbruikt: </span>'+verbruikt_gas;
         
        var max_temp = 'verborgen';
        var avg_temp = 'verborgen';
        var min_temp = 'verborgen';

        if ( $('#GasChart').highcharts().series[1].visible === true && $('#GasChart').highcharts().series[0].visible === true ){
            try {
                avg_temp = var_avg_temp.toFixed(1)+" °C";
                max_temp = var_max_temp.toFixed(1)+" °C";
                min_temp = var_min_temp.toFixed(1)+" °C";
            } catch(err) {} // suppress console error
        }

        if ( $('#GasChart').highcharts().series[1].visible === true && $('#GasChart').highcharts().series[0].visible === false ){
            try {
                avg_temp = var_avg_temp.toFixed(1)+" °C";
                max_temp = var_max_temp.toFixed(1)+" °C";
                min_temp = var_min_temp.toFixed(1)+" °C";
            } catch(err) {} // suppress console error
        }

        var max_temp_color = '#FF0000';
        var min_temp_color = '#0088FF';
        s += '<br/><span style="color: '+max_temp_color+'">maximum temperatuur: </span>'+max_temp;
        s += '<br/><span style="color: #384042">gemiddelde temperatuur: </span>'+avg_temp;
        s += '<br/><span style="color: '+min_temp_color+'">minimum temperatuur: </span>'   +min_temp;
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
    series: [ 
    {
	  yAxis: 0,
      visible: GseriesVisibilty[0],
      showInNavigator: true,
      name: 'm3 gas',
      type: 'column',
      color: '#507ABF',
      data: GverbrData,
      zIndex: 0,
    }, 
    {
      yAxis: 1,
      visible: GseriesVisibilty[1],
      showInNavigator: true,
      name: 'Temperatuur',
      data: Gaverages,
      type: 'spline',
      zIndex: 2,
      color: '#384042',
      lineWidth: 1,
      marker: {
        fillColor: 'white',
        lineWidth: 1,
        lineColor: '#384042'
      }
    },
    {
      yAxis: 1,
      dashStyle: 'ShortDot',
      visible: GseriesVisibilty[1],
      name: 'Range',
      data: Granges,
      type: 'areasplinerange',
      lineWidth: 1,
      linkedTo: ':previous',
      color: '#ff0000',
      negativeColor: '#0088FF',
      fillOpacity: 0.3,
      zIndex: 1,
      marker: {
        fillColor: 'white',
        lineWidth: 1,
        lineColor: '#ff0000'
      }
    }],
    plotOptions: {
      series: {
        showInNavigator: true,
        events: {
          legendItemClick: function () {
            // console.log('legendItemClick index='+this.index);
            if ( this.index === 0 ) {
              toLocalStorage('stat-d-gas-visible',!this.visible); // #PARAMETER
            }
            if ( this.index === 1 ) {
              toLocalStorage('stat-d-gas-temp-visible',!this.visible); // #PARAMETER
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
    var chart = $('#GasChart').highcharts();
    if( typeof(chart) !== 'undefined') {

        chart.series[0].setData( GverbrData );
        chart.series[1].setData( Gaverages );
        chart.series[2].setData( Granges );
        

      /*
      chart.series[0].update({
       data: GverbrData,
      });
      chart.series[1].update({
        data: Gaverages,
      });
      chart.series[2].update({
       data: Granges,
      });
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
        readJsonApiHistoryDay( maxrecords );
    }
    setTimeout('DataLoop()',1000);
}


$(function() {
  toLocalStorage('stats-menu-gas',window.location.pathname);
  GseriesVisibilty[0] = JSON.parse(getLocalStorage('stat-d-gas-visible'));  // #PARAMETER
  GseriesVisibilty[1] = JSON.parse(getLocalStorage('stat-d-gas-temp-visible')); // #PARAMETER
  Gselected = parseInt(getLocalStorage('stat-d-select-gas-index'),10); // #PARAMETER
  Highcharts.setOptions({
   global: {
    useUTC: false
    }
  });
  screenSaver( <?php echo config_read(79);?> ); // to enable screensaver for this screen.
  createGasChart();
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
        <?php page_menu_header_gas(0); ?> <!-- #PARAMETER -->
        <?php weather_info(); ?>
    </div>
</div>

<div class="mid-section">
    <div class="left-wrapper">
        <?php page_menu(5); ?>
        <div id="timerText" class="pos-8 color-timer"></div>
        <?php fullscreen(); ?>
    </div> 
    <div class="mid-content-2 pad-13">
    <!-- links -->
    	<div class="frame-2-top">
    		<span class="text-2">dagen (m<sup>3</sup> gas)</span>
    	</div>
    	<div class="frame-2-bot"> 
    	<div id="GasChart" style="width:100%; height:480px;"></div>	
    	</div>
</div>
</div>
<div id="loading-data"><img src="./img/ajax-loader.gif" alt="Even geduld aub." height="15" width="128" /></div>   

</body>
</html>