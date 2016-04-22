clientModule.factory('socket', function($rootScope){
	var socket = new WebSocket("ws://" + window.location.host + "/ws");
	var socketQueue = [];

	var clientSocket = {
		send: function(data){
			var socketSend = function(){
				socket.send(data);
			};
			if (socket.readyState === 1){
				socketSend();
			} else {
				socketQueue.push(socketSend);
			}
		}
	};

	socket.onopen = function(event){
		if (socketQueue.length > 0) {
			for (var i = 0; i < socketQueue.length; i++){
				socketQueue[i]();
			}
		}
		socketQueue = [];
	};

	socket.onmessage = function(event){
		$rootScope.$emit("socketmsg", event);
	};

	socket.close = function(event){
		console.log("socket closed");
	};

	return clientSocket;
});
