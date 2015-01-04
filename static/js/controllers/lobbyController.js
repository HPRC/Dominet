clientModule.controller("lobbyController", function($rootScope, $scope, socket, client){
	$scope.lobbyList = [];
	$scope.name = "";
	$scope.challenging = null;
	$scope.challengers = [];
	$scope.challenge = function(otherPlayer){
		$scope.challenging = otherPlayer;
		socket.send(JSON.stringify({"command": "challenge", "challenger": $scope.name, "otherPlayer": otherPlayer}));
	};

	$scope.cancel = function(){
		socket.send(JSON.stringify({"command": "cancel", "challenger": $scope.name, "otherPlayer": $scope.challenging}));
		$scope.challenging = null;
	};

	$scope.accept = function(challenger){
		for (var i=0; i<$scope.challengers.length; i++){
			$scope.decline($scope.challengers[i]);
			i--;
		}
		socket.send(JSON.stringify({"command": "startGame", "players": [$scope.name, challenger]}));
	};

	$scope.decline = function(challenger){
		$scope.challengers.splice($scope.challengers.indexOf(challenger),1);
		socket.send(JSON.stringify({"command": "decline", "challenger": challenger}));
	};

	$scope.unchallenged = function(json){
		$scope.challengers.splice($scope.challengers.indexOf(json.challenger),1);
	};

	$scope.challenged = function(json){
		$scope.challengers.push(json.challenger);
	};

	$scope.gotDeclined = function(json){
		$scope.challenging = null;
	};

	$scope.lobby = function(json){
		$scope.name = client.name;
		$scope.lobbyList = json.lobby_list;
	};

	$scope.resume = function(json){
		$scope.$apply(function(){
			$scope.main.game = true;	
		});
	};

	$scope.$on("$destroy", function(){
		socketlistener();
	});

	var socketlistener = $rootScope.$on("socketmsg", function(data, event){
		var jsonres = JSON.parse(event.data);
		if (jsonres.command === "init"){
			client.onmessage(event);
		}
		var exec = $scope[jsonres.command];
			if (exec != undefined){
				exec.call($scope,jsonres);
			}

		$scope.$digest();
	});
});