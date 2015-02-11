clientModule.factory('socket', function($rootScope){
	var socket = new WebSocket("ws://1ac1405d.ngrok.com/ws");
	socket.onopen = function(event){
		$("#msg").text("Waiting for other player...");
	};

	socket.onmessage = function(event){
		$rootScope.$emit("socketmsg", event);
	}

	socket.close = function(event){
		console.log("socket closed");
	};

	return socket;
});
