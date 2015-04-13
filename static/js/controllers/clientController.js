clientModule.controller("clientController", function($rootScope, $scope, socket, client, $sce, $timeout){
	client.initGameProperties();
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
	$scope.gameTrash = client.getGameTrash();
	$scope.gameLogs = client.getGameLogs();

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
			$scope.gameTrash = client.getGameTrash();
			$scope.gameLogs = client.getGameLogs();
			$scope.$evalAsync($timeout($scope.updateScroll), 0);
		});
	});


	

	$scope.updateScroll = function(){
		document.getElementById("container").scrollTop = document.height;
		document.getElementById("msg").scrollTop = document.getElementById("msg").scrollHeight;
	};

	$scope.returnLobby = function(){
		$scope.main.game = false;
		socket.send(JSON.stringify({"command": "returnToLobby"}));
	};

	$scope.renderHtml = function(html){
    	return $sce.trustAsHtml(html);
	};

});