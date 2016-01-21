clientModule.controller("helpModalController", function($scope, $uibModalInstance) {
	$scope.close = function(){
		$uibModalInstance.dismiss("cancel");
	};
});