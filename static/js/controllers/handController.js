clientModule.controller("handController", function($scope, client, cardStyle){
	$scope.disabled = function(card){
		if (card.type === "Victory" || card.type === "Curse" || $scope.turn === false || $scope.modeJson.mode === "wait"
			|| $scope.modeJson.mode === "select" || $scope.modeJson.mode === "selectSupply"){
			return true;
		}
		if ($scope.modeJson.mode === "buy"){
			if (card.type.indexOf("Action") !== -1 || $scope.modeJson.bought_cards === true){
				return true;
			}
		}
		return false;
	};

	$scope.clickCard = function(card){
		if ($scope.disabled(card)){
			return;
		}
		client.playCard(card);
	};

	$scope.getButtonStyle = function(card){
		if (!$scope.disabled(card)){
			return cardStyle.getButtonStyle(card);
		} else {
			return cardStyle.getButtonStyle(card) + " disabled-card";
		}
	};

});