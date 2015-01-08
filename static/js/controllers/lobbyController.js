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
		$scope.challengers.splice($scope.challengers.indexOf(challenger),1);
		socket.send(JSON.stringify({"command": "loadGame", "players": [$scope.name, challenger], "challenger": challenger}));
		decline_all();
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

	$scope.gotAccepted = function(json){
		$scope.challenging = null;
		decline_all();

	};

	$scope.lobby = function(json){
		$scope.name = client.name;
		$scope.lobbyList = json.lobby_list;
	};

	var decline_all = function(){
		for (var i=0; i<$scope.challengers.length; i++){
			$scope.decline($scope.challengers[i]);
			i--;
		}
	};

	$scope.resume = function(json){
		if ($scope.challenging !== null){
			$scope.cancel();
		}
		$scope.$apply(function(){
			$scope.main.game = true;
		});
	};

	$scope.announce = function(json){
		$("#gameChat").append("<br>" + json.msg);
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