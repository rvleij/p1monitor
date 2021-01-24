<?php
session_start(); #must be here for every page using login
include '/p1mon/www/util/auto_logout.php';
include '/p1mon/www/util/page_header.php';
include '/p1mon/www/util/p1mon-util.php';
include '/p1mon/www/util/menu_control.php';
include '/p1mon/www/util/p1mon-password.php';
include '/p1mon/www/util/config_buttons.php';
include '/p1mon/www/util/config_read.php';
include '/p1mon/www/util/textlib.php';
include '/p1mon/www/util/div_err_succes.php';
include '/p1mon/www/util/pageclock.php';

#print_r($_POST);
loginInit();
passwordSessionLogoutCheck();

$noInetCheck = isInternetIPAllowed();
$localip     = validLocalIpAdress(getClientIP());
//$localip        = False;
//$noInetCheck    = False;
if( $localip == False ){ 
        if( $noInetCheck == False ) {
            die();
        }
}

$err_cnt = -1;
/*
if ( isset($_POST["api"]) ) { 
	$err_cnt = 0;
	if ($_POST["api"] == '1' ) {
		#echo "on<br>";
		if ( updateConfigDb("update config set parameter = '1' where ID = 17"))$err_cnt += 1;
	} else {
		#echo "off<br>";
		if ( updateConfigDb("update config set parameter = '0' where ID = 17"))$err_cnt += 1;
	}
}

if ( isset($_POST["api_weather"]) ) { 
	if ( $err_cnt == -1 ) $err_cnt=0;
	if ($_POST["api_weather"] == '1' ) {
		#echo "on<br>";
		if ( updateConfigDb("update config set parameter = '1' where ID = 26"))$err_cnt += 1;
	} else {
		#echo "off<br>";
		if ( updateConfigDb("update config set parameter = '0' where ID = 26"))$err_cnt += 1;
	}
}

if ( isset($_POST["api_usage"]) ) { 
	if ( $err_cnt == -1 ) $err_cnt=0;
	if ($_POST["api_usage"] == '1' ) {
		#echo "on<br>";
		if ( updateConfigDb("update config set parameter = '1' where ID = 27"))$err_cnt += 1;
	} else {
		#echo "off<br>";
		if ( updateConfigDb("update config set parameter = '0' where ID = 27"))$err_cnt += 1;
	}
}

if ( isset($_POST["api_counter"]) ) { 
	if ( $err_cnt == -1 ) $err_cnt=0;
	if ($_POST["api_counter"] == '1' ) {
		#echo "on<br>";
		if ( updateConfigDb("update config set parameter = '1' where ID = 40"))$err_cnt += 1;
	} else {
		#echo "off<br>";
		if ( updateConfigDb("update config set parameter = '0' where ID = 40"))$err_cnt += 1;
	}
}


if ( isset($_POST["api_p1data"]) ) { 
	if ( $err_cnt == -1 ) $err_cnt=0;
	if ($_POST["api_p1data"] == '1' ) {
		#echo "on<br>";
		if ( updateConfigDb("update config set parameter = '1' where ID = 42"))$err_cnt += 1;
	} else {
		#echo "off<br>";
		if ( updateConfigDb("update config set parameter = '0' where ID = 42"))$err_cnt += 1;
	}
}
*/


?>
<!doctype html>
<html lang='NL'>
<head>
<title>API configuratie</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<link rel="shortcut icon" type="image/x-icon" href="/favicon.ico">
<link type="text/css" rel="stylesheet" href="./css/p1mon.css" />
<link type="text/css" rel="stylesheet" href="./font/roboto/roboto.css"/>

<script defer src="./font/awsome/js/all.js"></script>
<script src="./js/jquery.min.js"></script>
<script src="./js/p1mon-util.js"></script>
</head>
<body>
<script>
var initloadtimer

    function readJsonApiList(){ 
        $.getScript( "./api/v1/catalog", function( data, textStatus, jqxhr ) {
        try {
            htmlString = "<ol type='1'>";
            var jsondata = JSON.parse(data); 
            for (var j =0;  j<jsondata.length; j++){    
				splitBuf = jsondata[j].split('/');            // get rid of IP adres for url
				url = jsondata[j].replace(splitBuf[0],'.');   // get rid of IP adres for url
				htmlString = htmlString + "<li><a href='" + url + "' target='_blank'>" + jsondata[j] + "</a></li>";
        	}
			htmlString = htmlString + "</ol>";
			$('#apiList').append( htmlString );
      	} catch(err) {}
   	});
    }

    function LoadData() {
        clearTimeout(initloadtimer);
        /*
        readJsonApi();
        readJsonWeatherApi();
        readJsonUsageApi();
        readJsonCounterApi();
        */
        initloadtimer = setInterval(function(){LoadData();}, 5000);
    }    

    /*
    function readJsonCounterApi() { 
        $.getScript( "/json/apiV2countervalue.php", function( data, textStatus, jqxhr ) {
            try {
                $('#APIpreCounter').html(text2Json( data ));
            } catch(err) {}
        });
    }
    
    function readJsonUsageApi() { 
        $.getScript( "/json/apiV3usage.php", function( data, textStatus, jqxhr ) {
            try {
                $('#APIusagepre').html(text2Json( data ));
            } catch(err) {
				console.log( err );
			}
        });
    }
    
    function readJsonWeatherApi() { 
        $.getScript( "/json/apiV2weather.php", function( data, textStatus, jqxhr ) {
            try {
                $('#APIweatherpre').html(text2Json( data ));
            } catch(err) {}
        });
    }
    
    function readJsonApi() { 
        $.getScript( "./json/apiV4basic.php", function( data, textStatus, jqxhr ) {
            try {
				$('#APIpre').html(text2Json( data ));
            } catch(err) { 
				console.log( err );
			}
        });
    }
    */

    $(function () {
        /*
        checkShowOption('#APIusageDetail');
        checkShowOption('#APIweatherDetail');
        checkShowOption('#APIbasicDetail');
        checkShowOption('#APIcounterDetail');
        checkShowOption('#APIp1dataDetail');
        */

        readJsonApiList()
        LoadData();
    });

    /*
    function checkShowOption(item) {
        if ( getLocalStorage(item) !== null ) { 
            if (getLocalStorage(item) == 1) {
                $(item).show();
            }
        }
    }
    */
    /*
    function apiDetails(item) {
        console.log(item);
        if( $(item).css('display') == 'block' ) {
            toLocalStorage(item,0);
            $(item).hide();
        } else {
            $(item).show();
            toLocalStorage(item,1);
        }
    }
    */
</script>
  <div class="top-wrapper">
            <div class="content-wrapper">
                 <?php page_header();?>
            </div>
        </div>

        <div class="top-wrapper-2">
            <div class="content-wrapper pad-13">
                <!-- header 2 -->
                <?php pageclock(); ?>
            </div>
            <?php config_buttons(1);?>
        </div> <!-- end top wrapper-2 -->

        <div class="mid-section">
            <div class="left-wrapper-config"> <!-- left block -->
                <?php menu_control(5);?>
            </div>

            <div id="right-wrapper-config"> <!-- right block -->
            <!-- inner block right part of screen -->
				<div id="right-wrapper-config-left">
					<!-- start of content -->
					<form name="formvalues" id="formvalues" method="POST">

					<div class="frame-4-top">
							<span class="text-15">API lijst</span>
						</div>
						<div class="frame-4-bot">
							<div class='pad-12'>
								<div id="apiList">
								<!-- dynamicly filled -->
								</div>
							</div>
						</div>
						<p></p>	

						<!-- placeholder variables for session termination -->
						<input type="hidden" name="logout" id="logout" value="">
					</form>
				</div>
				
				<div id="right-wrapper-config-right">
					<div class="frame-4-top">
						<span class="text-15">hulp</span>
					</div>
					<div class="frame-4-bot text-10">	
						<?php echo strIdx(8);?>
					</div>
					
					</div>
				</div>
			
			<!-- end inner block right part of screen -->
	</div>	
	<?php echo div_err_succes();?>
	<?php echo autoLogout(); ?>
</body>
</html>