clientModule.controller("infoController", function($scope, client, $sce){
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
});
