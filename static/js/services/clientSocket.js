clientModule.factory('socket', function($rootScope){
	var socket = new WebSocket("ws://" + window.location.hostname + "/ws");
	socket.onopen = function(event){

	};

	socket.onmessage = function(event){
		$rootScope.$emit("socketmsg", event);
	};

	socket.close = function(event){
		console.log("socket closed");
	};

	return socket;
});
