<?php
    require_once('settings.php');

    $height = $_GET['height'];
    $width = $_GET['width'];
    $pfid = $_GET['pfid'];

    $command = escapeshellcmd($script_path." ".$pfid." ".$width." ".$height);
    shell_exec($command);
?>