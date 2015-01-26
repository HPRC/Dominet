clientModule.controller("infoController", function($scope, $sce){
	$scope.renderHtml = function(html)
	{
    	return $sce.trustAsHtml(html);
	};

});
