clientModule.factory('socket', function(){
	var socket = new WebSocket("ws://192.168.0.101:9999/ws");
	return socket;
});
