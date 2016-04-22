clientModule.controller("clientController", function($rootScope, $scope, socket, client, favicon, $sce, $timeout){
	
	var updateScopeClient = function(){
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
		$scope.gameLog = $sce.trustAsHtml(client.getGameLog());
		$scope.gameMat = client.getGameMat();
	};
	
	$scope.c = client;	
	client.initGameProperties();
	socket.send(JSON.stringify({"command": "ready", "name": client.name}));
	updateScopeClient();

	var socketlistener = $rootScope.$on("socketmsg", function(data, event){
		client.onmessage(event);
		$scope.$apply(function(){
			updateScopeClient();
			$scope.deckSize = client.getDeckSize();
			$scope.discardSize = client.getDiscardSize();
			//update scroll after angular renders changes to dom
			$scope.$evalAsync($timeout($scope.updateScroll), 0);
		});
	});

	$scope.$on("$destroy", function(){
		socketlistener();
	});

	$scope.updateScroll = function(){
		document.getElementById("container").scrollTop = document.height;
		document.getElementById("msg").scrollTop = document.getElementById("msg").scrollHeight;
	};

	$scope.returnLobby = function(){
		$scope.main.game = false;
		socket.send(JSON.stringify({"command": "returnToLobby"}));
		favicon.stopAlert();
	};

});