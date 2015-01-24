clientModule.controller("clientController", function($rootScope, $scope, socket, client){
	$scope.c = client;
	$scope.hand = client.getHand();
	$scope.turn = client.getTurn();
	$scope.actions = client.getActions();
	$scope.buys = client.getBuys();
	$scope.balance = client.getBalance();
	$scope.kingdom = client.getKingdom();
	$scope.baseSupply = client.getBaseSupply();
	$scope.spendableMoney = client.getSpendableMoney();
	$scope.modeJson = client.getModeJson();

	$scope.$on("$destroy", function(){
		socketlistener();
	});
	socket.send(JSON.stringify({"command": "ready", "name": client.name}));
	var socketlistener = $rootScope.$on("socketmsg", function(data, event){
		client.onmessage(event);
		$scope.$apply(function(){
			$scope.hand = client.getHand();
			$scope.turn = client.getTurn();
			$scope.actions = client.getActions();
			$scope.buys = client.getBuys();
			$scope.balance = client.getBalance();
			$scope.kingdom = client.getKingdom();
			$scope.baseSupply = client.getBaseSupply();
			$scope.spendableMoney = client.getSpendableMoney();
			$scope.modeJson = client.getModeJson();
			$scope.deckSize = client.getDeckSize();
			$scope.discardSize = client.getDiscardSize();
		});
	});

	$scope.returnLobby = function(){
		$scope.main.game = false;
		socket.send(JSON.stringify({"command": "returnToLobby"}));
	};

});