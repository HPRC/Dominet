(function() {
	var clientModule = angular.module("clientApp", []);

	clientModule.service('socket', function(){
		var socket = new WebSocket("ws://localhost:9999/ws");
		return socket;

	});

	clientModule.controller("clientController", function($scope, socket){
		var constructor = function() {
			this.id = null;
			this.name = null;
			this.turn = false;
			this.hand = [];
			this.kingdom = {};
			this.actions = 0;
			this.buys = 0;
			this.balance = 0;
			this.played = [];
			this.spendableMoney = 0;
			//mode overidden by turn
			this.modeJson = {"mode":"action"}; //.mode = action, buy, select, wait
			this.socket = socket;
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
						$scope.spendableMoney = c.getSpendableMoney();
						$scope.modeJson = c.getModeJson();
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

		constructor.prototype.updateHand = function(json){
			this.hand = JSON.parse(json.hand);
		};

		constructor.prototype.announce = function(json){
				$('#msg').append("<br>" + json.msg);
				$("#container").scrollTop($(document).height());
		};

		constructor.prototype.chat = function(json){
				$("#gameChat").append("<br><b>" + json.speaker + ": </b>" + json.msg);
				$("#scrollChat").scrollTop($("#scrollChat")[0].scrollHeight);
		};

		constructor.prototype.kingdomCards = function(json){
			var kingdomArray = JSON.parse(json.data);
			for (var i=0; i< kingdomArray.length; i++) {
				this.kingdom[kingdomArray[i].title] = kingdomArray[i];			
			}
			console.log(this.kingdom);
		};

		constructor.prototype.startTurn = function(json){
			this.turn = true;
			this.updateResources(json);
			this.spendableMoney = 0;
			this.updateSpendable();
		};

		constructor.prototype.updateMode = function(json){
			this.modeJson = json;
		};

		constructor.prototype.endTurn = function(){
			this.turn = false;
			this.discard(this.hand);
			this.discard(this.played);
			this.played = [];
			this.socket.send(JSON.stringify({"command": "endTurn"}));
		};

		constructor.prototype.discard = function(cards){
			if (cards.length == 0){
				return;
			}
			var cardsByTitle = $.map(cards, function(val, index){
				return val.title;
			});
			this.socket.send(JSON.stringify({"command": "discard", "cards": cardsByTitle}));
			//remove from hand
			for (var j=0; j<cards.length; j++){
				for (var i=0; i<this.hand.length; i++){
					if (cards[j] == this.hand[i]){
						this.hand.splice(i,1);
						i--;
					}
				}
			}
		};

		constructor.prototype.updateSpendable = function (){
			this.spendableMoney = 0;
			for (var i=0; i<this.hand.length; i++){
				if (this.hand[i].type === "Money"){
					this.spendableMoney += this.hand[i].value;
				}
			}
		};

		constructor.prototype.spendAllMoney = function(){
			this.spendableMoney = 0;
			this.modeJson = {"mode":"buy"};
			for (var i=0; i<this.hand.length; i++){
				if (this.hand[i].type === "Money"){
					this.playCard(this.hand[i]);
					i--;
				}
			}
		};

		constructor.prototype.playCard = function(card){
			if (this.actions > 0 || card.type.indexOf("Action") === -1){
				this.socket.send(JSON.stringify({"command":"play", "card": card.title}));
				this.played.push(card);
				//remove from hand
				for (var i=0; i<this.hand.length; i++){
					if (card == this.hand[i]){
						this.hand.splice(i,1);
						i--;
					}
				}
			}
			if (card.type === "Money"){
				this.modeJson = {"mode":"buy"};
				this.updateSpendable();
			}
		};

		constructor.prototype.buyCard = function(card){
			if (this.balance >= card.price){
				this.buys -= 1;
				this.balance -= card.price;
				this.socket.send(JSON.stringify({"command":"buyCard", "card": card.title}));
			}
		};

		constructor.prototype.updatePiles = function(json){
			this.kingdom[json.card].count = json.count;
		};

		constructor.prototype.updateResources = function(json){
			this.actions = json.actions;
			this.buys = json.buys;
			this.balance = json.balance;
		};

		constructor.prototype.modeDefault = function(){
			if (this.actions > 0){
				this.modeJson = {"mode":"action"};
			} else {
				this.modeJson = {"mode":"buy"};
			}
		}

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
		};

		constructor.prototype.getSpendableMoney = function(){
			return this.spendableMoney;
		};

		constructor.prototype.getModeJson = function(){
			return this.modeJson;
		};

		var c = new constructor();
		$scope.c = c;
		$scope.hand = c.getHand();
		$scope.turn = c.getTurn();
		$scope.actions = c.getActions();
		$scope.buys = c.getBuys();
		$scope.balance = c.getBalance();
		$scope.kingdom = c.getKingdom();
		$scope.spendableMoney = c.getSpendableMoney();
		$scope.modeJson = c.getModeJson();

	});
	
	clientModule.controller("handController", function($scope){
		$scope.disabled = function(card){
			if (card.type === "Victory" || $scope.turn === false || $scope.modeJson.mode === "wait"){
				return true;
			}
			if ($scope.modeJson.mode === "buy"){
				if (card.type.indexOf("Action") !== -1){
					return true;
				}
			}
			return false;
		};

		$scope.clickCard = function(card){
			$scope.c.playCard(card);
		};

	});

	clientModule.controller("kingdomController", function($scope){
		$scope.getKingdomArray = function(){
			return $.map($scope.kingdom, function(card, title){
				return card;
			});
		};

		$scope.disabled = function(){
			return (!$scope.turn || $scope.modeJson.mode === "wait");
		};

		$scope.getButtonStyle = function(card){
			var colorDict = {
				"Money": "btn btn-warning",
				"Victory": "btn btn-success",
				"Action|Attack": "btn btn-danger"
			};

			if (card.type in colorDict){
				return colorDict[card.type];
			} else {
				return "btn btn-default";
			}
		}

	});

	clientModule.controller("selectController", function($scope){
		$scope.canBeDone = false;
		$scope.selected = [];
		$scope.check = function(card, isChecked){
			var checkedCount = $("input:checkbox:checked").length;
			if (checkedCount >= $scope.modeJson.count){
				$("input:checkbox").not(":checked").attr("disabled", true);
				$scope.canBeDone = true;
			} else {
				$("input:checkbox").not(":checked").attr("disabled", false);
				$scope.canBeDone = false;
			}

			if (isChecked){
				$scope.selected.push(card);
			} else {
				var i = $scope.selected.indexOf(card);
				$scope.selected.splice(i,1);
			}
		};

		$scope.doneSelection = function(){
			var doThis = $scope.modeJson.doToSelect;
			if ($scope.c[doThis]){
				$scope.c[doThis]($scope.selected);
				$scope.modeJson = $scope.c.modeDefault();
				$scope.c.socket.send(JSON.stringify({"command": "unwait"}));
			} else {
				console.log(doThis + " not found!?");
			}
		};

	});

})();

