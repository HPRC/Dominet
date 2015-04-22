clientModule.factory('socket', function($rootScope){
	var socket = new WebSocket("ws://7a34688c.ngrok.com/ws");
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
