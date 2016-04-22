clientModule.controller("lobbyController", function($rootScope, $scope, $uibModal, gameTable, socket, client){
	$scope.lobbyList = [];
	$scope.gameTables = [];
	$scope.atTable = false;
	$scope.newGameTable = gameTable;

	socket.send(JSON.stringify({
		"command": "getLobby"
	}));

	$scope.lobby = function(json){
		$scope.name = client.getName();
		$scope.lobbyList = json.lobby_list;
		$scope.gameTables = json.game_tables;
	};

	$scope.createGameTable = function(){
		$scope.atTable = true;
		socket.send(JSON.stringify({
			"command": "createTable", 
			"table": $scope.newGameTable
		}));
		$scope.newGameTable.title == "";
	};

	$scope.joinTable = function(table){
		if (table.players.length < table.seats){
			$scope.atTable = true;
			socket.send(JSON.stringify({
				"command": "joinTable",
				"host": table.host
			}));
		}
	};

	$scope.leaveTable = function(table){
		$scope.atTable = false;
		socket.send(JSON.stringify({
			"command": "leaveTable",
			"host": table.host
		}));
	};

	$scope.startGame = function(table){
		socket.send(JSON.stringify({
			"command": "startGame",
			"host": table.host
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

  $scope.usingIncludes = function(table){
      return table.required.join(", ");
  };

  $scope.usingExcludes = function(table){
      return table.excluded.join(", ");
  };

  $scope.supplyInfo = function(table){
      return table.req_supply;
  };

	$scope.openAdvGameModal = function () {
		var modal = $uibModal.open({
			templateUrl: '/static/js/directives/advGameModal.html',
			controller: 'advGameModalController',
			resolve: {
				advGame: function(){
					return $scope.newGameTable;
				}
			}
		});

		modal.result.then( function (newGameTable) {
			$scope.newGameTable = newGameTable;
			$scope.createGameTable();
		});
	};

	$scope.$on("$destroy", function(){
		socketlistener();
	});

	var socketlistener = $rootScope.$on("socketmsg", function(data, event){
		var jsonres = JSON.parse(event.data);
		var exec = $scope[jsonres.command];
		if (exec != undefined){
			exec.call($scope, jsonres);
		}

		$scope.$digest();
	});
});


