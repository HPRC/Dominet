clientModule.controller("advGameModalController", function(gameTable, $scope, $modalInstance) {
	$scope.newGameTable = gameTable;
	$scope.inputRequired = "";
    $scope.inputExcluded = "";
    $scope.supplyRadio = {
        value: "default"
    };

	$scope.createGame = function(){
		$scope.newGameTable.required = $scope.inputRequired.split(',');
        $scope.newGameTable.excluded = $scope.inputExcluded.split(',');
        $scope.newGameTable.req_supply = $scope.supplyRadio.value;
		$modalInstance.close($scope.newGameTable);
	};

	$scope.cancel = function(){
		$modalInstance.dismiss("cancel");
	};
});