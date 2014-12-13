

var client = (function() {

	var constructor = function() {
		this.id = null;
		this.name = null;
		this.socket = new WebSocket("ws://localhost:9999/ws");
		var that = this;

		this.socket.onopen = function(event){
			$("#msg").text("Waiting for other player...");
		};

		this.socket.onmessage = function(event){
			var jsonres = JSON.parse(event.data);
			var exec = that[jsonres.command];
			if (exec != undefined){
				exec.call(that,jsonres);
			}
		};

		this.socket.close = function(event){
			console.log("socket closed");
		};


		$("#endTurn").click(function(){
			that.socket.send(JSON.stringify({"command": "endTurn"}))
			$("#playerOptions").css('visibility', 'hidden');
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

	constructor.prototype.init = function(json) {
			this.id = json.id;
			this.name = json.name;
	};

	constructor.prototype.initGame = function(json){
		var that = this;
		var hand = JSON.parse(json.hand);
		for (var i=0; i<hand.length; i++){
			var c = $('<button/>', {
				  type: 'button',
				  text: hand[i].title,
				  click: function(n) {
				  	return function(){
					  	if (hand[n].type !== "Victory"){
					  		that.socket.send(JSON.stringify({"command": "play", "card": hand[n] .title}));
					  	}
				  	};
			  	}(i)
			});
			$("#hand").append(c);
		}
	};

	constructor.prototype.announce = function(json){
			$('#msg').append("<br>" + json.msg);
	};

	constructor.prototype.chat = function(json){
			$("#gameChat").append("<br><b>" + json.speaker + ": </b>" + json.msg);
	};

	constructor.prototype.startTurn = function(json){
			$("#actions").text(json.actions);
			$("#buys").text(json.actions);
			$("#balance").text(json.balance);
			$("#playerOptions").css('visibility', 'visible');
	};



	return constructor;

}());

$(document).ready(function(){
	var c = new client();
});