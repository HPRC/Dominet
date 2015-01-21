clientModule.controller("supplyController", function($scope, socket, client, cardStyle){
	var getSupplyArray = function(supply){
		return $.map(supply, function(card, title){
			return card;
		});
	};

	$scope.kingdomSupplyArray = getSupplyArray($scope.kingdom);
	$scope.baseSupplyArray = getSupplyArray($scope.baseSupply);

    $scope.$watch('kingdom', function(newValue, oldValue) {
		$scope.kingdomSupplyArray = getSupplyArray($scope.kingdom);
	}, true);
    $scope.$watch('baseSupply', function(newValue, oldValue) {
		$scope.baseSupplyArray = getSupplyArray($scope.baseSupply);
	}, true);

	$scope.disabled = function(card){
		if (card.title in $scope.kingdom && $scope.kingdom[card.title].count === 0 || 
			card.title in $scope.baseSupply && $scope.baseSupply[card.title].count === 0){
			return true;
		}

		if ($scope.turn && $scope.modeJson.mode === "buy"){
			return card.price > $scope.balance;
		}
		if ($scope.modeJson.mode === "gain"){
			if ($scope.modeJson.equal_only){
				return card.price !== $scope.modeJson.price;
			} else {
				return card.price > $scope.modeJson.price;
			}
		}
		return (!$scope.turn || $scope.modeJson.mode === "wait" || $scope.modeJson.mode === "action");
	};

	$scope.clickCard = function(card){
		if ($scope.modeJson.mode === "gain"){
			//refactor into method (?)
			socket.send(JSON.stringify({"command": "gain", "card": card.title}));
		} else {
			client.buyCard(card);
		}
	};

	$scope.getButtonStyle = cardStyle.getButtonStyle;
});