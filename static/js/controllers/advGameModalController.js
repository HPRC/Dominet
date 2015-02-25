clientModule.controller("advGameModalController", function(gameTable, $scope, $modalInstance) {
	$scope.newGameTable = gameTable;
	$scope.inputRequired = "";

	$scope.createGame = function(){
		$scope.newGameTable.requiredCards = $scope.inputRequired.split(',');
		$modalInstance.close($scope.newGameTable);
	};

	$scope.cancel = function(){
		$modalInstance.dismiss("cancel");
	};
});