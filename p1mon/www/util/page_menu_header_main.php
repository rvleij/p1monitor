<?php
function page_menu_header_main($id) {
$m0=$m1=$m2=$m3=$m4=$m5='';

switch ($id) {
	case 0: /* home */
        $m0= "menu-active";
       	break;
    case 1: /* grafiek */
    	$m1 = "menu-active";
		break;
	case 2: /* grafiek */
    	$m2 = "menu-active";
        break;
	default:
	/* default value so always a menu is available */
	$m0="menu-active";
}
echo <<< EOT
 <div class="pad-13 content-wrapper">
	<div class="pos-7 content-wrapper $m0"><a href="main-1.php" class="$m0">verbruik & levering</a></div>
	<div class="pos-7 content-wrapper $m1"><a href="main-2.php" class="$m1">verbruik</a></div>
</div>
EOT;
}
?>
