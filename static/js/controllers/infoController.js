clientModule.controller("infoController", function($scope, client, $sce, $modal){
	$scope.renderHtml = function(html)
	{
    	return $sce.trustAsHtml(html);
	};

	$scope.trashDisplay = function(trash)
	{
		if (trash.length == 0) {
			return "Trash:<br> -"
		}
		return "Trash:<br>" + trash
	};

    $scope.openReportBugModal = function () {
		var modal = $modal.open({
			templateUrl: '/static/js/directives/reportBugModal.html',
			controller: 'reportBugModalController'
		});
	};
});
