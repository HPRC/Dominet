clientModule.controller("supplyController", function($scope, socket, client, cardStyle, favicon){
	var getSupplyArray = function(supply){
		arr = [];
		for (var key in supply){
			arr.push(supply[key]);
		}
		return arr;
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
		if ((card.title in $scope.kingdom && $scope.kingdom[card.title].count === 0 || 
			card.title in $scope.baseSupply && $scope.baseSupply[card.title].count === 0) 
			&& $scope.modeJson.allow_empty !== true){
			return true;
		}

		if ($scope.turn && $scope.modeJson.mode === "buy"){
			return $scope.getPrice(card) > $scope.balance;
		}

        //if (($scope.turn && $scope.modeJson.mode === "buy") && ($scope.contraband.size > 0)) {
        //    return $scope.contraband[card.title] ? true : false;
        //}

		if ($scope.modeJson.mode === "selectSupply"){
			if ($scope.modeJson.type_constraint !== null && card.type.indexOf($scope.modeJson.type_constraint) === -1){
				return true;
			} else {
				if ($scope.modeJson.equal_only){
					return $scope.getPrice(card) !== $scope.modeJson.price;
				} else if ($scope.modeJson.price){
					return $scope.getPrice(card) > $scope.modeJson.price;
				} else {
                    return false
                }

			}
		}
		return (!$scope.turn || $scope.modeJson.mode === "wait" ||  $scope.modeJson.mode === "select" || $scope.modeJson.mode === "action");
	};


	$scope.clickCard = function(card){
		if ($scope.disabled(card)){
			return;
		}
		if ($scope.modeJson.mode === "selectSupply"){
			//wait to update ui until server responds
			client.updateMode({"mode":"wait"});
			//refactor into method (?)
			favicon.stopAlert();
			socket.send(JSON.stringify({"command": "selectSupply", "card": [card.title]}));
		} else {
			client.buyCard(card);
		}
	};

	$scope.getPrice = function(card){
		if (card.price + client.getPriceModifier() <= 0){
			return 0;	
		} else {
			return card.price + client.getPriceModifier();
		}
	};

    $scope.selectNone = function() {
    	favicon.stopAlert();
        socket.send(JSON.stringify({"command": "selectSupply", "card": ["None"]}));
    };

	$scope.getButtonStyle = function(card){
		if (!$scope.disabled(card)){
			return cardStyle.getButtonStyle(card);
		} else {
			return cardStyle.getButtonStyle(card) + " disabled-card";
		}
	};
});
