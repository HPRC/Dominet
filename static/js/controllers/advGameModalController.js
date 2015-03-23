clientModule.controller("advGameModalController", function(gameTable, $scope, $modalInstance) {
	$scope.newGameTable = gameTable;
	$scope.inputRequired = "";
    $scope.inputExcluded = "";
    $scope.prosperitySupplyCheckbox = {
        value: false
    };

	$scope.createGame = function(){
		$scope.newGameTable.required = $scope.inputRequired.split(',');
        $scope.newGameTable.excluded = $scope.inputExcluded.split(',');
        $scope.newGameTable.prosperitySupply = $scope.prosperitySupplyCheckbox.value;
		$modalInstance.close($scope.newGameTable);
	};

	$scope.cancel = function(){
		$modalInstance.dismiss("cancel");
	};
});