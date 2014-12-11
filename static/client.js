

var client = (function() {

	var constructor = function() {
		this.id = null;
		this.name = null;
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

		$("#sendChat").click(function(){
			var msg = $("#inputChat").val();
			msg = msg.replace(/</g, "&lt;").replace(/>/g, "&gt;");
			that.socket.send(JSON.stringify({"command": "chat", "msg": msg}))
		});

		$("#inputChat").keypress(function(e){
			if(e.which==13){
				var msg = $("#inputChat").val();
				msg = msg.replace(/</g, "&lt;").replace(/>/g, "&gt;");
				that.socket.send(JSON.stringify({"command": "chat", "msg": msg}))
				$("#inputChat").val("");
			}
		});
	};

	constructor.prototype = {
		init: function(json) {
			this.id = json.id;
			this.name = json.name;
		},

		initGame: function(json){
			console.log("let the games begin" + json.player1 + " vs "+ json.player2);
		},

		announce: function(json){
			$('#msg').append("<br>" + json.msg);
		},

		startTurn: function(json){
			$("#endTurn").css('visibility', 'visible');
		},

		chat: function(json){
			$("#gameChat").append("<br><b>" + json.speaker + ": </b>" + json.msg);
		}
	};
	return constructor;

}());

$(document).ready(function(){
	var c = new client();
});