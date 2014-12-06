var client = (function() {

	var constructor = function() {
		this.id = null;
		var that = this;
		this.socket = new WebSocket("ws://localhost:9999/ws");
			
		this.socket.onopen = function(event){
			$("#msg").text("Waiting for other player...");
		};

		this.socket.onmessage = function(event){
			var jsonres = JSON.parse(event.data);
			var exec = that[jsonres.command];
			if (exec != undefined){
				exec(jsonres);
			}
		};

		this.socket.close = function(event){
			console.log("socket closed");
		};

		$("#endTurn").click(function(){
			that.socket.send(JSON.stringify({"command": "endTurn"}))
			$("#endTurn").css('visibility', 'hidden');
		});

	};

	constructor.prototype = {
		init: function(json) {
			this.id = json.id;
		},

		initGame: function(json){
			console.log("let the games begin" + json.player1 + " vs "+ json.player2);
		},

		announce: function(json){
			$('#msg').append("<br>" + json.msg);
		},

		startTurn: function(json){
			$("#endTurn").css('visibility', 'visible');
		}
	};
	return constructor;

}());

$(document).ready(function(){
	var c = new client();
});