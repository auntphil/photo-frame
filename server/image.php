<?php
	header('Access-Control-Allow-Origin: *'); 
	//Pulling Settings
    $rawSettings = file_get_contents("settings.json");
    $settings = json_decode($rawSettings, true);
    //Checking if Frame is set
    if(!isset($_GET['frame']) || !isset($_GET['height']) || !isset($_GET['width'])){exit();}
    $frame = $_GET['frame'];
	$frameHeight = $_GET['height'];
	$frameWidth = $_GET['width'];
   
    //Checking if Frame is known
    if(array_key_exists($frame, $settings['frames'])){
        try {
			$conn = "pgsql:host=".$settings['db']['host'].";port=".$settings['db']['port'].";dbname=".$settings['db']['db'].";";
			// make a database connection
			$pdo = new PDO($conn, $settings['db']['username'], $settings['db']['password'], [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
		
			if ($pdo) {
				$newPhoto = True;
				while ($newPhoto) {
					$imgInfo = $pdo->query("select unit.filename, folder.name from unit inner join many_item_has_many_normal_album on many_item_has_many_normal_album.id_item = unit.id_item inner join folder on unit.id_folder = folder.id where many_item_has_many_normal_album.id_normal_album = ". $settings['frames'][$frame]['album'])->fetchAll();
					$randomImg = $imgInfo[rand(0,(count($imgInfo)-1))];
					if( !str_ends_with(strtolower($randomImg[0]), 'mp4') ){
						$newPhoto = False;
					}
				}
				$path = $settings['app']['photo_root'].$randomImg[1].'/'.$randomImg[0];
				$background = new Imagick($path);
				$foreground = new Imagick($path);

				//Getting Image Orientation
				$exifArray = $foreground->getImageProperties("exif:Orientation");
				foreach ($exifArray as $name => $property)
				{
					switch($property){
						case 6:
							$background->rotateimage("black",270);
							$foreground->rotateimage("black",270);
							break;
						case 8:
							$background->rotateimage("black",90);
							$foreground->rotateimage("black",90);
							break;
					}
				}

				//Getting Image Size
				$imageprops = $background->getImageGeometry();
				$width = $imageprops['width'];
				$height = $imageprops['height'];
				
				//Ratio
				$frameRatio = $frameWidth / $frameHeight;
				$imageRatio = $width / $height;
				
				/**
				 * Background Blur
				 */
				//Background Size
				$resizeWidth = $frameWidth * 1.3;
				$resizeHeight = ($resizeWidth / $imageRatio) * 1.3;
				
				//Finding Top Left Corner
				if($resizeWidth !== $frameWidth){
					$TLx = floor(($resizeWidth - $frameWidth)/2);
				}else{
					$TLx = 0;
				}
				if($resizeHeight !== $frameHeight){
					$TLy = floor(($resizeHeight - $frameHeight)/2);
				}else{
					$TLy = 0;
				}
				
				$background->resizeImage($width*0.15,$height*0.15, imagick::FILTER_LANCZOS, 0.9, true);
				$background->blurImage(0, 6, Imagick::CHANNEL_DEFAULT);
				$background->resizeImage($resizeWidth,$resizeHeight, imagick::FILTER_LANCZOS, 0.9, true);
				$background->cropImage($frameWidth, $frameHeight, $TLx, $TLy);
				
				/**
				 * Foreground Image
				 */
				//Foreground Size
				if($width > $height){
					#Landscape
					$resizeHeight = $frameHeight;
					$resizeWidth = $frameHeight * $imageRatio;
				}else{
					#Portrait
					$resizeHeight = $frameHeight;
					$resizeWidth = $frameHeight * $imageRatio;
				}
				$foreground->resizeImage($resizeWidth,$resizeHeight, imagick::FILTER_LANCZOS, 0.9, true);

				/**
				 * Combine Images
				 */
				//Finding Top Left Corner
				if($resizeWidth !== $frameWidth){
					$TLx = floor(($frameWidth - $resizeWidth)/2);
				}else{
					$TLx = 0;
				}

				$background->compositeImage($foreground, \Imagick::COMPOSITE_ATOP, $TLx, 0);

				foreach ($exifArray as $name => $property)
				{
					switch($property){
						case 6:
							$background->rotateimage("black",90);
							$foreground->rotateimage("black",90);
							break;
						case 8:
							$background->rotateimage("black",270);
							$foreground->rotateimage("black",270);
							break;
					}
				}

				header('Content-type: image/jpg');  
				echo $background;
			}
		} catch (PDOException $e) {
			die($e->getMessage());
		} finally {
			if ($pdo) {
				$pdo = null;
			}
		}
    }
?>