clientModule.factory('socket', function($rootScope){
	// http://c675bd8.ngrok.com
    var socket = new WebSocket("ws://c675bd8.ngrok.com/ws");
	// var socket = new WebSocket("ws://localhost:9999/ws");
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
