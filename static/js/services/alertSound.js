clientModule.factory('alertSound', function(){
	var sound = new Audio('/static/Dalert.mp3');

	this.playSound = function(){	
		sound.play();
	};

	return {
		playSound: this.playSound
	};
});