clientModule.factory('socket', function($rootScope){
	var socket = new WebSocket("ws://localhost:9999/ws");
    //var socket = new WebSocket("ws://3f850448.ngrok.com/ws");
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
