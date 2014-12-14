(function() {
	var clientModule = angular.module("clientApp", []);

	clientModule.controller("clientController", function($scope){
		var constructor = function() {
			this.id = null;
			this.name = null;
			this.turn = false;
			this.hand = null;
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
					$scope.$apply(function(){
						$scope.hand = that.hand;
					});
				}
			};

			this.socket.close = function(event){
				console.log("socket closed");
			};


			$("#endTurn").click(function(){
				this.turn = false;
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
			this.hand = JSON.parse(json.hand);
			console.log(this.hand);
			for (var i=0; i<hand.length; i++){
				var c = $('<button/>', {
					  type: 'button',
					  text: that.hand[i].title,
					  click: function(n) {
					  	return function(){
						  	if (that.hand[n].type !== "Victory"){
						  		that.socket.send(JSON.stringify({"command": "play", "card": that.hand[n] .title}));
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

		constructor.prototype.getHand = function(){
			return this.hand;
		};

		constructor.prototype.getTurn = function(){
			return this.turn;
		};

		constructor.prototype.startTurn = function(json){
				this.turn = true;
				$("#actions").text(json.actions);
				$("#buys").text(json.actions);
				$("#balance").text(json.balance);
				$("#playerOptions").css('visibility', 'visible');
		};

		var c = new constructor();
		$scope.hand = c.getHand();
		$scope.turn = c.getTurn();
	});

})();

