clientModule.factory('socket', function($rootScope){
	var socket = new WebSocket("ws://10b7e0a1.ngrok.com/ws");
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
