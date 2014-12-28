clientModule.factory('socket', function(){
	var socket = new WebSocket("ws://192.168.2.40:9999/ws");
	return socket;
});
