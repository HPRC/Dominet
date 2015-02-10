clientModule.controller("lobbyController", function($rootScope, $scope, socket, client){
	$scope.lobbyList = [];
	$scope.gameTables = [];
	$scope.name = "";
	$scope.atTable = false;

	$scope.newGameTable = {title:"", seats:2};

	$scope.lobby = function(json){
		console.log(json);
		$scope.name = client.name;
		$scope.lobbyList = json.lobby_list;
		$scope.gameTables = json.game_tables;
	};

	$scope.resume = function(json){
		if ($scope.challenging !== null){
			$scope.cancel();
		}
		$scope.$apply(function(){
			$scope.main.game = true;
		});
	};

	$scope.createGameTable = function(){
		if ($scope.newGameTable.title !== ""){
			$scope.atTable = true;
			socket.send(JSON.stringify({
				"command": "createTable", 
				"table": $scope.newGameTable
			}));
		}
	};

	$scope.joinTable = function(table){
		$scope.atTable = true;
		socket.send(JSON.stringify({
			"command": "joinTable",
			"host": table.host,
			"joiner": $scope.name
		}));
	};

	$scope.leaveTable = function(table){
		$scope.atTable = false;
		socket.send(JSON.stringify({
			"command": "leaveTable",
			"host": table.host,
			"leaver": $scope.name
		}));
	};

	$scope.playersToString = function(table){
		var array = table.players.slice();
		for (var i=0; i< table.seats - table.players.length; i++){
			array.push("----");	
		}
		return array.join(", ");
	};

	$scope.announce = function(json){
		$("#gameChat").append("<br>" + json.msg);
	};

	$scope.isAtTable = function(table){
		return table.players.indexOf($scope.name) !== -1;
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