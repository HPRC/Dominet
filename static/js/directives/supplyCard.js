clientModule.directive('supplyCard', function($sce){
	return {
		restrict: 'EA',
		templateUrl: '/static/js/directives/supplyCard.html',
		link: function(scope, elm, attrs) {
      scope.descriptionHtml = $sce.trustAsHtml(scope.card.description);
		}
	};
});