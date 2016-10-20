clientModule.factory('favicon', function($interval, alertSound){
	var flashing = null;
	//isActive boolean for tracking if we are showing the red or alerted color favicon
	var isActive = false;
	document.head = document.head || document.getElementsByTagName('head')[0];

	var change = function(url){
		var linkobj = document.createElement("link");
		var currentFavicon = document.getElementById("favicon");
		linkobj.id = "favicon";
		linkobj.href = url;
		linkobj.rel="shortcut icon"
		if (currentFavicon){
			document.head.removeChild(currentFavicon);
		}
		document.head.appendChild(linkobj);
	};

	this.alertFavicon = function(){
		alertSound.playSound();
		if (flashing === null){
			flashing = $interval(function(){
				if (isActive){
					change("static/favicon.ico");
					isActive = false;
					document.title = "Dominet"
				} else {
					change("static/favicon_red.ico");
					isActive = true;
					document.title = "Your Move!"
				}
			}, 800, 0, false);
		}
	};


	this.stopAlert = function(){
		if (flashing !== null){
			$interval.cancel(flashing);
			favicon.href = "static/favicon.ico";
			document.title = "Dominet"
			isActive = false;
			flashing = null;
		}
	};

	return {
		alertFavicon: this.alertFavicon,
		stopAlert: this.stopAlert
	};
});