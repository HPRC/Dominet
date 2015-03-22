clientModule.factory('socket', function($rootScope){
    var socket = new WebSocket("ws://62a8e2e5.ngrok.com/ws");
    //var socket = new WebSocket("ws://localhost:9999/ws");
	socket.onopen = function(event){
		$("#msg").text("Waiting for other player...");
	};

	socket.onmessage = function(event){
		$rootScope.$emit("socketmsg", event);
	};

	socket.close = function(event){
		console.log("socket closed");
	};

	return socket;
});
