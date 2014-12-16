(function() {
	var clientModule = angular.module("clientApp", []);

	clientModule.controller("clientController", function($scope){
		var constructor = function() {
			this.id = null;
			this.name = null;
			this.turn = false;
			this.hand = null;
			this.kingdom = [];
			this.actions = 0;
			this.buys = 0;
			this.balance = 0;
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
					//TODO refactor
					$scope.$apply(function(){
						$scope.hand = c.getHand();
						$scope.turn = c.getTurn();
						$scope.actions = c.getActions();
						$scope.buys = c.getBuys();
						$scope.balance = c.getBalance();
						$scope.kingdom = c.getKingdom();
					});
				}
			};

			this.socket.close = function(event){
				console.log("socket closed");
			};

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
			this.hand = JSON.parse(json.hand);
		};

		constructor.prototype.announce = function(json){
				$('#msg').append("<br>" + json.msg);
		};

		constructor.prototype.chat = function(json){
				$("#gameChat").append("<br><b>" + json.speaker + ": </b>" + json.msg);
		};

		constructor.prototype.kingdomCards = function(json){
			this.kingdom = JSON.parse(json.data);
			console.log(this.kingdom);
		};

		constructor.prototype.startTurn = function(json){
			this.turn = true;
			this.updateUi(json);
		};

		constructor.prototype.endTurn = function(){
			this.turn = false;
			this.socket.send(JSON.stringify({"command": "endTurn"}));
		};

		constructor.prototype.playCard = function(title){
			this.socket.send(JSON.stringify({"command":"play", "card": title}));
		};

		constructor.prototype.updateUi = function(json){
			this.actions = json.actions || this.actions;
			this.buys = json.buys || this.buys;
			this.balance = json.balance || this.balance;
		};

		constructor.prototype.getHand = function(){
			return this.hand;
		};

		constructor.prototype.getTurn = function(){
			return this.turn;
		};

		constructor.prototype.getActions = function(){
			return this.actions;
		};

		constructor.prototype.getBalance = function(){
			return this.balance;
		};

		constructor.prototype.getBuys = function(){
			return this.buys;
		};

		constructor.prototype.getKingdom = function(){
			return this.kingdom;
		}

		var c = new constructor();
		$scope.c = c;
		$scope.hand = c.getHand();
		$scope.turn = c.getTurn();
		$scope.actions = c.getActions();
		$scope.buys = c.getBuys();
		$scope.balance = c.getBalance();
		$scope.kingdom = c.getKingdom();
	});
	
	clientModule.controller("handController", function($scope){
		$scope.show = true;
		$scope.disabled = function(card){
			if (card.type === "Victory" || $scope.turn === false){
				return true;
			}
			return false;
		};

		$scope.clickCard = function(card){
			$scope.c.playCard(card);
			$scope.show = false;
		}

	});
	// clientModule.directive("handCard", function(){
	// 	return {
	// 		restrict: 'EA',
	// 		template: '<button>{{card.title}}</button>',
	// 		compile: function(element, attributes){
	// 			var link = function(scope, element, attributes){
	// 				var card = JSON.parse(attributes.card);
	// 				if (card.type === "Victory"){
	// 					//how to disable
	// 				}
	// 				element.bind('click', function(){
	// 					element.css('display', 'none');
	// 					scope.c.playCard(card.title);
	// 				});
	// 			};
	// 			return link
	// 		}
	// 	};
	// });

})();

