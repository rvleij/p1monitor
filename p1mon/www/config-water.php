<?php
session_start(); #must be here for every page using login
include '/p1mon/www/util/auto_logout.php';
include '/p1mon/www/util/page_header.php';
include '/p1mon/www/util/p1mon-util.php';
include '/p1mon/www/util/menu_control.php';
include '/p1mon/www/util/p1mon-password.php';
include '/p1mon/www/util/config_buttons.php';
include '/p1mon/www/util/config_read.php';
include '/p1mon/www/util/updateStatusDb.php';
include '/p1mon/www/util/textlib.php';
include '/p1mon/www/util/pageclock.php';

//print_r($_POST);
loginInit();
passwordSessionLogoutCheck();
$err_cnt = -1;
$file_name = '/p1mon/mnt/ramdisk/watermeter-counter-reset.status';

$noInetCheck = isInternetIPAllowed();
$localip     = validLocalIpAdress(getClientIP());
//$localip        = False;
//$noInetCheck    = False;
if( $localip == False ){ 
        if( $noInetCheck == False ) {
            die();
        }
}

#print_r($_POST);
$showStatusOutput = 0;
if ( isset($_POST["fs_rb_watermeter_reset"]) ) {
    if ( $_POST[ "fs_rb_watermeter_reset" ] == '1' ) {
        # remove status file
        unlink( $file_name );
        writeSemaphoreFile('watermeter_counter_reset');
        $showStatusOutput = 1;
        ##echo "<br>action=" . $showStatusOutput . "<br>";
    }
}

function makeSelectortGPIO( $id ) {
    $configValue = config_read( $id );
    for ( $i=2; $i<28; $i++ ) {
        if ( $configValue == $i ) {
            $selected = 'selected="selected"';
        } else {
            $selected = '';
        }
        echo '<option ' . $selected. ' value="'. $i . '" >GPIO' . $i .'</option>';
    }

}

if ( isset( $_POST["fs_rb_watermeter"] ) ) { //ok
    if ( $err_cnt == -1 ) $err_cnt=0;
    if ( $_POST[ "fs_rb_watermeter" ] == '1' ) {
        if ( updateConfigDb("update config set parameter = '1' where ID = 96") ) $err_cnt += 1;
    } else {
        if ( updateConfigDb("update config set parameter = '0' where ID = 96") ) $err_cnt += 1;
    }
}

if( isset($_POST["puls_liter_value"]) ) { //ok
    if ( $err_cnt == -1 ) $err_cnt=0;
    $float = (float)inputClean($_POST["puls_liter_value"]);
    if ( $float > 1000 or $float < 0 ) { $float=1; }
    if ( updateConfigDb("update config set parameter = '" . (string)$float . "' where ID = 98"))  $err_cnt += 1;
}

if( isset($_POST["water_m3_value"]) ) { //ok
    if ( $err_cnt == -1 ) $err_cnt=0;
    $float = (float)inputClean($_POST["water_m3_value"]);
    if ( $float > 1000000 or $float < 0 ) { $float=0; }
    if ( updateConfigDb("update config set parameter = '" . (string)$float . "' where ID = 99"))  $err_cnt += 1;
}

if( isset($_POST["timestamp_watermeter"]) ) { //ok
    if ( $err_cnt == -1 ) $err_cnt=0;
    
    $val = timestampClean( $_POST["timestamp_watermeter"] );
    if ( strlen( $val ) != 19 ) {
        $val = '';
    } 
    if ( updateConfigDb("update config set parameter = '" .$val . "' where ID = 100") )  $err_cnt += 1;
}

if( isset($_POST["gpio_water"]) ) { //ok
    if ( $err_cnt == -1 ) $err_cnt=0;
    $int = (int)inputClean($_POST["gpio_water"]);
    $configValue = config_read( 97 );
    #echo "<br>";
    #echo $int . "<br>";
    #echo $configValue  . "<br>";
    if ( $int !=  $configValue ) { // create load only do when there is a change
        writeSemaphoreFile( 'water_gpio' );  
    }
    if ( updateConfigDb( "update config set parameter = '" . (string)$int . "' where ID = 97") )  $err_cnt += 1;
}

?>
<!doctype html>
<html lang="nl">
<head>
<title>Energie levering configuratie</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<link rel="shortcut icon" type="image/x-icon" href="/favicon.ico">
<link type="text/css" rel="stylesheet" href="./css/p1mon.css" />
<link type="text/css" rel="stylesheet" href="./font/roboto/roboto.css"/>
<script defer src="./font/awsome/js/all.js"></script>
<script src="./js/jquery.min.js"></script>
<script src="./js/p1mon-util.js"></script>
<script src="./js/jquery.validate.min.js"></script>
<script src="./js/moment-link/moment-with-locales.min.js"></script>

</head>
<body>
<script>
var initloadtimer;

function readJsonApiStatus(){ 
    $.getScript( "./api/v1/status", function( data, textStatus, jqxhr ) {
      try {
        var jsonarr = JSON.parse(data); 
        for (var j=0;  j<jsonarr.length; j++){   
                switch(jsonarr[j][0]) {
                    case 90:
                        $('#watermeter_puls_timestamp').text( jsonarr[j][1] );
                        break;
            }
        }
      } catch(err) {
          console.log( err );
      }
   });
}

function readJsonApiHistoryPowerDay( cnt ){ 
    $.getScript( "/api/v2/watermeter/day?limit=" + cnt, function( data, textStatus, jqxhr ) {
        try {
        var jsondata = JSON.parse(data); 
        if ( jsondata.length == 0 ) {
            $('#verbruikWater').html( padXX( 0 ,5, 3 ) + '&nbsp;m&#179;');
 
        } else {
            $('#verbruikWater').html( padXX( jsondata[0][5]  ,5, 3 ) + '&nbsp;m&#179;' );
        }
      } catch(err) {}
   });
}

function readUpgradeLogging(){ 
    $.get( '/txt/txt-water-reset-status.php', function( response, status, xhr ) {
        if ( status == "error" ) {
            $("#upgrade_asssist_logging").html('Data niet beschikbaar.');
        }
        if ( response.length > 0 ) {
            $('#upgrade_asssist_logging').html( response );
        } else {
            if ( document.getElementById('upgrade_asssist_logging').innerHTML.length < 60 ) { // prevent the flashing of the log window.
                $('#upgrade_asssist_logging').html( "<b>Even geduld aub, gegevens worden verwerkt.</b><br>" );
            }
        }
    }); 
}

function LoadData() {
    timout_setting = 2000
    clearTimeout(initloadtimer);
    readJsonApiStatus();
    readJsonApiHistoryPowerDay( 1 );
    if ( document.getElementById('counter_status').style.display == "block" ) {
        readUpgradeLogging();
        timout_setting = 150;
    }
    initloadtimer = setInterval( function(){ LoadData(); }, timout_setting );
}

$(function () {
    centerPosition('#counter_status');
    LoadData();
});


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
        <?php config_buttons(0);?>
        </div> <!-- end top wrapper-2 -->

        <div class="mid-section">
            <div class="left-wrapper-config"> <!-- left block -->
                <?php menu_control( 16 );?>
            </div>
            
            <div id="right-wrapper-config"> <!-- right block -->
            <!-- inner block right part of screen -->
                <div id="right-wrapper-config-left-4">
                    <!-- start of content -->
                    <form name="formvalues" id="formvalues" method="POST">

                        <div class="frame-4-top">
                            <span class="text-15">watermeter</span>
                        </div>
                        <div class="frame-4-bot">
                           
                            <div class="float-left">
                                <p class="p-1"></p>
                                <i class="text-10 pad-14 fas fa-map-pin"></i>
                                <label class="text-10">GPIO pin selectie</label> 
                                <p class="p-1"></p>
                                <i class="pad-7 text-10 fas fa-toggle-off"></i>
                                <label class="text-10">Watermeter puls meting actief</label>
                                <p class="p-1"></p>
                                <i class="pad-7 text-10 fas fa-tint"></i>
                                <label class="text-10" title='<?php echo strIdx( 84 );?>'>puls waarde in Liter</label>
                                <p class="p-1"></p>
                                <i class="pad-27 text-10 fas fa-tint"></i>
                                <label class="text-10" title='<?php echo strIdx( 85 );?>'>watermeter stand in m&#179;</label>
                                <p class="p-1"></p>
                                <i class="pad-27 text-10 far fa-clock"></i>
                                <label class="text-10" title='<?php echo strIdx( 86 );?>'>meterstand timestamp</label>
                                <p class="p-1"></p>
                                <i class="pad-7 text-10 fas fa-toggle-off"></i>
                                <label class="text-10" title='<?php echo strIdx( 87 );?>'>meterstand reset</label>
                                <p class="p-1"></p>
                                <i class="pad-7 text-10 fas fa-tint"></i>
                                <label class="text-10" title='<?php echo strIdx( 89 );?>'>watermeter stand</label>
                                <p class="p-1"></p>
                                <i class="pad-7 text-10 far fa-clock"></i>
                                <label class="text-10" title='<?php echo strIdx( 90 );?>'>tijdstip water puls</label>
                            </div>
                            <div class="float-right pad-1">
                                <p class="p-1"></p>
                                <select class="select-1 color-select color-input-back cursor-pointer" name="gpio_water" id="gpio_water">
                                    <?php makeSelectortGPIO( 97 ) ;?>
                                </select>
                                <p class="p-1"></p>
                                <div class=''>
                                    <input class="cursor-pointer" id="fs_rb_watermeter_on"  name="fs_rb_watermeter" type="radio" value="1" <?php if ( config_read( 96 ) == 1 ) { echo 'checked'; }?>>Aan
                                    <input class="cursor-pointer" id="fs_rb_watermeter_off" name="fs_rb_watermeter" type="radio" value="0" <?php if ( config_read( 96 ) == 0 ) { echo 'checked'; }?>>Uit
                                </div>
                                <p class="p-1"></p>
                                <input title='<?php echo strIdx( 92 );?>' class="input-13 color-settings color-input-back" id="puls_liter_value" name="puls_liter_value" type="text" value="<?php echo config_read( 98 );?>">
                                <p class="p-1"></p>
                                <input title='<?php echo strIdx( 93 );?>' class="input-13 color-settings color-input-back" id="water_m3_value" name="water_m3_value" type="text" value="<?php echo config_read( 99 );?>">
                                <p class="p-1"></p>
                                
                                <input title='<?php echo strIdx( 96 );?>' placeholder="YYYY-MM-DD HH:MM:00" class="input-14 color-settings color-input-back" id="timestamp_watermeter" name="timestamp_watermeter" type="text" value="<?php echo config_read( 100 );?>" >
                                <p class="p-1"></p>

                                <div title='<?php echo strIdx( 94 );?>'>
                                    <input class="cursor-pointer" id="fs_rb_watermeter_reset_on"  name="fs_rb_watermeter_reset" type="radio" value="1">Aan
                                    <input class="cursor-pointer" id="fs_rb_watermeter_reset_off" name="fs_rb_watermeter_reset" type="radio" value="0" checked>Uit
                                </div>
                                <p class="p-1"></p>
                                <div title='<?php echo strIdx( 97 );?>' class="text-10 pad-20" ><span id="verbruikWater">onbekend</span></div>
                                <p class="p-1"></p>
                                
                                
                                <div title='<?php echo strIdx( 95 );?>' class="text-10 pad-20" ><span id="watermeter_puls_timestamp">onbekend</span></div>
                            </div>
                        </div>
                        <p></p>
                        
                        <!-- placeholder variables for session termination -->
                        <input type="hidden" name="logout" id="logout" value="">
                    </form>
                </div>

                <div id="right-wrapper-config-right-4">
                    <div class="frame-4-top">
                        <span class="text-15">hulp</span>
                    </div>
                    <div class="frame-4-bot text-10">
                        <img class="pos-1" alt="PI GPIO pin layout" src="./img/pin_layout.svg">
                    </div>
                </div>
            </div>
            <!-- end inner block right part of screen -->
    </div>

    <!-- start block -->
    <div id="counter_status" class="pos-45" style="display: none" >
        <div class='close_button-2' id="assist_logging_close">
            <i class="color-select fas fa-times-circle" data-fa-transform="grow-6"" aria-hidden="true"></i>
        </div>
    <div class="frame-4-top">
        <span class="text-15">Meterstand reset logging</span>
            </div>
                <div class="frame-4-bot">
                    <div id="upgrade_asssist_logging" class="text-9">
                     
                    </div>
                </div>
        </div>
    </div>
    <!-- end block -->

    <script>

jQuery.validator.addMethod("ztatz_time_format", function(value, element) {
    if ( value.length == 0 ) {
        //console.log( "ztatz_time_format value is empty" );
        return true;
    }
    // console.log( "ztatz_time_format" );
    if ( /^[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1]) (2[0-3]|[01][0-9]):[0-5][0-9]:[0-5][0-9]$/.test(value) ) {
        //console.log ( moment(value).isValid() );
        return moment(value).isValid();
    } else {
        return false;
    };
}, '');

jQuery.validator.addMethod("ztatz_gpio", function(value, element) {
        if ( document.getElementById("gpio_water").value == document.getElementById("gpio_list").value ) {
            return false;
        }
        if ( document.getElementById("gpio_water").value == document.getElementById("gpio_list_tarif").value ) {
            d
            return false;
        }   
        document.getElementById("gpio_list").style.borderColor = "#a6a6a6";
        return true;
}, '');

$(function() {
    $("#formvalues").validate({
        rules: {
            'gpio_water':{
                required: false,
                //ztatz_gpio:true
            },
            'timestamp_watermeter': {
                required: false,
                //minlength: 19,
                //maxlength: 19,
                ztatz_time_format: true
            },
            'water_m3_value': {
                required: true,
                number: true,
                max: 1000000,
                min: 0
            },
            'puls_liter_value': {
                required: true,
                number: true,
                max: 1000,
                min: 0
            }
        },
        invalidHandler: function(e, validator) { 
            var errors = validator.numberOfInvalids();
            //console.log ( errors );
          },
        errorPlacement: function(error, element) {
            $(this).addClass('error');
            //console.log ( 'errorPlacement' );
            return false;  // will suppress error messages    
        }
    }); 
});

$('#assist_logging_close').click(function() {    
   hideStuff('counter_status');
});

centerPosition('#counter_status');

</script>
<?php 
if ( $showStatusOutput == 1 ) {
    echo "<script>showStuff('counter_status');</script>";
}
echo autoLogout();?>
</body>
</html>