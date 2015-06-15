clientModule.controller("infoController", function($scope, client, $sce, $modal){
	$scope.renderHtml = function(html)
	{
    	return $sce.trustAsHtml(html);
	};

	$scope.matDisplay = function(mat_name, data){
		if (data.length === 0){
			return $scope.renderHtml(mat_name + ":<br> -");
		}
		return $scope.renderHtml(mat_name + ":<br>" + data);
	};

    $scope.openReportBugModal = function () {
		var modal = $modal.open({
			templateUrl: '/static/js/directives/reportBugModal.html',
			controller: 'reportBugModalController'
		});
	};
});
