clientModule.controller("advGameModalController", function(gameTable, $scope, $uibModalInstance) {
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
		$uibModalInstance.close($scope.newGameTable);
	};

	$scope.cancel = function(){
		$uibModalInstance.dismiss("cancel");
	};
});