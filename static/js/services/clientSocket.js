clientModule.factory('socket', function(){
	var socket = new WebSocket("ws://localhost:9999/ws");
	return socket;
});
