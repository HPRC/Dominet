clientModule.controller("selectController", function($scope, socket, client){
    $scope.$watch('modeJson', function(newValue, oldValue) {
		if ($scope.modeJson.min_cards){
			$scope.canBeDone = false;
		} else {
			$scope.canBeDone = true;
		}
	});

	$scope.selected = [];
	//order in which the index checkbox was checked
	//key = index, value = order
	$scope.ordering = {};
	$scope.check = function(option, isChecked, index){
		var inputElements = document.getElementsByTagName("input");
		var checkedBoxes = [];
		var uncheckedBoxes = [];
		for (var i=0; i<inputElements.length; i++){
			if (inputElements[i].type === "checkbox"){
				if (inputElements[i].checked){
					checkedBoxes.push(inputElements[i]);
				} else {
					uncheckedBoxes.push(inputElements[i]);
				}
			}
		}
		var checkedCount = checkedBoxes.length;
		if ($scope.modeJson.min_cards !== undefined || $scope.modeJson.max_cards !== undefined){
			if ($scope.modeJson.min_cards !== undefined){
				if (checkedCount >= $scope.modeJson.min_cards){
					$scope.canBeDone = true;
				} else {
					$scope.canBeDone = false;
				}
			}
			if ($scope.modeJson.max_cards !== undefined){
				if (checkedCount == $scope.modeJson.max_cards){
					uncheckedBoxes.map(function(elem){
						elem.setAttribute("disabled", true);
					});
				} else {
					uncheckedBoxes.map(function(elem){
						elem.removeAttribute("disabled");
					});
				}
			}
		}

		if (isChecked){
			$scope.ordering[index] = checkedCount;
			$scope.selected.push(option);
		} else {
			//decrement all orderings before this key before deleting it after its unchecled
			for (var key in $scope.ordering){
				if ($scope.ordering[key] > $scope.ordering[index]){
					$scope.ordering[key]--;
				}
			}
			delete $scope.ordering[index]
			var i = $scope.selected.indexOf(option);
			$scope.selected.splice(i,1);
		}
	};

	$scope.checkboxOrder = function(card, index){
		return "#" + $scope.ordering[index];
	};

	$scope.selectOne = function(option){
		$scope.selected.push(option);
		$scope.doneSelection();
	};

	$scope.doneSelection = function(){
		client.updateMode({"mode":"wait"});

		//we reverse the selection array because on the server cards are stored [bottom, top]
		socket.send(JSON.stringify({"command": "post_selection", "selection": $scope.selected.reverse(), "act_on":$scope.modeJson.act_on}));
		$scope.selected = [];
	};

});
