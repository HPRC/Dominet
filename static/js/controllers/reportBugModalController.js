clientModule.controller("reportBugModalController", function($scope, $modalInstance, socket) {
    $scope.text = "";
	$scope.cancel = function(){
		$modalInstance.dismiss("cancel");
	};

    $scope.submitBugReport = function(){
        socket.send(JSON.stringify({
			"command": "submitBugReport",
            "text": $scope.text
		}));
        $modalInstance.close($scope.newGameTable);
    }
});