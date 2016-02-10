clientModule.controller("reportBugModalController", function($scope, $uibModalInstance, socket) {
    $scope.text = "";
	$scope.cancel = function(){
		$uibModalInstance.dismiss("cancel");
	};

    $scope.submitBugReport = function(){
        socket.send(JSON.stringify({
			"command": "submitBugReport",
            "text": $scope.text
		}));
        $uibModalInstance.close($scope.newGameTable);
    }
});