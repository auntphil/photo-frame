<?php
	ini_set('display_errors', 1);
	ini_set('display_startup_errors', 1);
	error_reporting(E_ALL);

	header('Access-Control-Allow-Origin: *'); 
	//Pulling Settings
    $rawSettings = file_get_contents("settings.json");
    $settings = json_decode($rawSettings, true);
    //Checking if Frame is set
    if(!isset($_GET['frame'])){exit();}
    $frame = $_GET['frame'];
	$frameHeight = $settings['frames'][$frame]['height'];
	$frameWidth = $settings['frames'][$frame]['width'];
	
	//Fixed Orientation of Photo
	function autorotate(Imagick $image)
	{
		switch ($image->getImageOrientation()) {
			case Imagick::ORIENTATION_TOPLEFT:
				break;
			case Imagick::ORIENTATION_TOPRIGHT:
				$image->flopImage();
				break;
			case Imagick::ORIENTATION_BOTTOMRIGHT:
				$image->rotateImage("#000", 180);
				break;
			case Imagick::ORIENTATION_BOTTOMLEFT:
				$image->flopImage();
				$image->rotateImage("#000", 180);
				break;
			case Imagick::ORIENTATION_LEFTTOP:
				$image->flopImage();
				$image->rotateImage("#000", -90);
				break;
			case Imagick::ORIENTATION_RIGHTTOP:
				$image->rotateImage("#000", 90);
				break;
			case Imagick::ORIENTATION_RIGHTBOTTOM:
				$image->flopImage();
				$image->rotateImage("#000", 90);
				break;
			case Imagick::ORIENTATION_LEFTBOTTOM:
				$image->rotateImage("#000", -90);
				break;
				default: // Invalid orientation
				break;
			}
		$image->setImageOrientation(Imagick::ORIENTATION_TOPLEFT);
	}
	
    //Checking if Frame is known
    if(array_key_exists($frame, $settings['frames'])){
		try {
			$db = new SQLite3('/var/piframe/images.db');
			$image = null;
			$results = $db->query("SELECT path, year FROM pictures WHERE month = '{$settings['frames'][$frame]['album']}' ORDER BY RANDOM() LIMIT 1;");
			while ($row = $results->fetchArray()) {
				$image = $row;
			}
			if ($image) {
				$newPhoto = True;
				
								
				$path = $image['path'];
				$background = new Imagick($path);
				$foreground = new Imagick($path);
				
				autorotate($background);
				autorotate($foreground);
				
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

				//Creating Font
				$draw = new ImagickDraw();
				$draw->setFillColor('black');
				$draw->setFont('PermanentMarker-Regular.ttf');
				$draw->setFontSize(45);
				$draw->setGravity(Imagick::GRAVITY_SOUTHEAST);
				$draw->setStrokeColor('white');
				$draw->setStrokeWidth(1);
				
				//Placing year onto photo
				$foreground->annotateImage($draw, 50, 50, -15, $image['year']);
				$foreground->setImageFormat('jpg');

				//Combining Foreground and Background
				$background->compositeImage($foreground, \Imagick::COMPOSITE_ATOP, $TLx, 0);
			
				$background->setImageFormat('jpg');
				ob_get_clean();
				header('Content-type: image/jpg');  
				echo $background;
			}
		} catch (Exception $e) {
			die($e->getMessage());
		} finally {
			
		}
    }
?>