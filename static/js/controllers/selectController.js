clientModule.controller("selectController", function($scope, socket){
    $scope.$watch('modeJson', function(newValue, oldValue) {
		if ($scope.modeJson.min_cards){
			$scope.canBeDone = false;
		} else {
			$scope.canBeDone = true;
		}
	});

	$scope.selected = [];
	$scope.check = function(option, isChecked){
		if ($scope.modeJson.min_cards !== undefined || $scope.modeJson.max_cards !== undefined){
			var checkedCount = $("input:checkbox:checked").length;
			if ($scope.modeJson.min_cards !== undefined){
				if (checkedCount >= $scope.modeJson.min_cards){
					$scope.canBeDone = true;
				} else {
					$scope.canBeDone = false;
				}
			}
			if ($scope.modeJson.max_cards !== undefined){
				if (checkedCount == $scope.modeJson.max_cards){
					$("input:checkbox").not(":checked").attr("disabled", true);
				} else {
					$("input:checkbox").not(":checked").attr("disabled", false);
				}
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
