clientModule.controller("selectController", function($scope, socket){
    $scope.$watch('modeJson', function(newValue, oldValue) {
		if ($scope.modeJson.count){
			$scope.canBeDone = false;
		} else {
			$scope.canBeDone = true;
		}
	});

	$scope.selected = [];
	$scope.check = function(option, isChecked){
		if ($scope.modeJson.count != undefined){
			var checkedCount = $("input:checkbox:checked").length;
			if (checkedCount >= $scope.modeJson.count){
				$("input:checkbox").not(":checked").attr("disabled", true);
				$scope.canBeDone = true;
			} else {
				$("input:checkbox").not(":checked").attr("disabled", false);
				$scope.canBeDone = false;
			}
		}

		if (isChecked){
			$scope.selected.push(option);
		} else {
			var i = $scope.selected.indexOf(option);
			$scope.selected.splice(i,1);
		}
	};

	$scope.selectOne = function(option){
		$scope.selected.push(option);
		$scope.doneSelection();
	};

	$scope.doneSelection = function(){
		socket.send(JSON.stringify({"command": "post_selection", "selection": $scope.selected, "act_on":$scope.modeJson.act_on}));
		$scope.selected = [];
	};

});
