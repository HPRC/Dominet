(function() {
	var clientModule = angular.module("clientApp", []);

	clientModule.factory('socket', function(){
		var socket = new WebSocket("ws://localhost:9999/ws");
		return socket;

	});

	clientModule.factory('client', function(socket, $rootScope) {
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
			this.modeJson = {"mode":"action"}; //.mode = action, buy, select, gain, wait
			var that = this;

			//socket
			this.onmessage = function(event){
				var jsonres = JSON.parse(event.data);
				var exec = that[jsonres.command];
				if (exec != undefined){
					exec.call(that,jsonres);
				}
			};

			$("#sendChat").click(function(){
				var msg = $("#inputChat").val();
				msg = msg.replace(/</g, "&lt;").replace(/>/g, "&gt;");
				socket.send(JSON.stringify({"command": "chat", "msg": msg}))
			});

			$("#inputChat").keypress(function(e){
				if(e.which==13){
					var msg = $("#inputChat").val();
					msg = msg.replace(/</g, "&lt;").replace(/>/g, "&gt;");
					socket.send(JSON.stringify({"command": "chat", "msg": msg}))
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
			this.updateSpendable();
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
			console.log(json);
			this.modeJson = json;
		};

		constructor.prototype.endTurn = function(){
			this.turn = false;
			this.discard(this.hand);
			this.played = []; //discarded on backend
			socket.send(JSON.stringify({"command": "endTurn"}));
		};

		constructor.prototype.discard = function(cards){
			if (cards.length == 0){
				return;
			}
			var cardsByTitle = $.map(cards, function(val, index){
				return val.title;
			});
			socket.send(JSON.stringify({"command": "discard", "cards": cardsByTitle}));
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
				socket.send(JSON.stringify({"command":"play", "card": card.title}));
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
				socket.send(JSON.stringify({"command":"buyCard", "card": card.title}));
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
		return new constructor();
	});

	clientModule.controller("clientController", function($scope, socket, client){
		$scope.c = client;
		$scope.hand = client.getHand();
		$scope.turn = client.getTurn();
		$scope.actions = client.getActions();
		$scope.buys = client.getBuys();
		$scope.balance = client.getBalance();
		$scope.kingdom = client.getKingdom();
		$scope.spendableMoney = client.getSpendableMoney();
		$scope.modeJson = client.getModeJson();
		socket.onopen = function(event){
			$("#msg").text("Waiting for other player...");
		};

		socket.onmessage = function(event){

			client.onmessage(event);

			$scope.$apply(function(){
				$scope.hand = client.getHand();
				$scope.turn = client.getTurn();
				$scope.actions = client.getActions();
				$scope.buys = client.getBuys();
				$scope.balance = client.getBalance();
				$scope.kingdom = client.getKingdom();
				$scope.spendableMoney = client.getSpendableMoney();
				$scope.modeJson = client.getModeJson();
			});
		};

		socket.close = function(event){
			console.log("socket closed");
		};
	});
	
	clientModule.controller("handController", function($scope, client){
		$scope.disabled = function(card){
			if (card.type === "Victory" || $scope.turn === false || $scope.modeJson.mode === "wait"
				|| $scope.modeJson.mode === "select" || $scope.modeJson.mode === "gain"){
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
			client.playCard(card);
		};

	});

	clientModule.controller("kingdomController", function($scope, socket, client){
		$scope.getKingdomArray = function(){
			return $.map($scope.kingdom, function(card, title){
				return card;
			});
		};

		$scope.disabled = function(card){
			if ($scope.modeJson.mode === "gain"){
				if ($scope.modeJson.equal_only){
					return card.price !== $scope.modeJson.price;
				} else {
					return card.price > $scope.modeJson.price;
				}
			}
			return (!$scope.turn || $scope.modeJson.mode === "wait");
		};

		$scope.clickCard = function(card){
			if ($scope.modeJson.mode === "gain"){
				//refactor into method (?)
				socket.send(JSON.stringify({"command": "gain", "card": card.title}));
			} else {
				client.buyCard(card);
			}
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

	clientModule.controller("selectController", function($scope, socket){
		if ($scope.modeJson.count){
			$scope.canBeDone = false;
		} else {
			$scope.canBeDone = true;
		}
		$scope.selected = [];
		$scope.check = function(card, isChecked){
			console.log($scope.modeJson);
			if ($scope.modeJson.count != undefined){
				var checkedCount = $("input:checkbox:checked").length;
				if (checkedCount >= $scope.modeJson.count){
					$("input:checkbox").not(":checked").attr("disabled", true);
					$scope.canBeDone = true;
				} else {
					$("input:checkbox").not(":checked").attr("disabled", false);
					$scope.canBeDone = false;
				}
			}

			if (isChecked){
				$scope.selected.push(card);
			} else {
				var i = $scope.selected.indexOf(card);
				$scope.selected.splice(i,1);
			}
		};

		$scope.selectOne = function(card){
			$scope.selected.push(card);
			$scope.doneSelection();
		};

		$scope.doneSelection = function(){
			var cardsByTitle = $.map($scope.selected, function(val, index){
				return val.title;
			});
			socket.send(JSON.stringify({"command": "unwait", "selection": cardsByTitle	, "card":$scope.modeJson.card}));
			$scope.selected = [];
		};

	});

})();

