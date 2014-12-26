clientModule.directive('supplyCard', function(){
	return {
		restrict: 'EA',
		templateUrl: '/static/js/directives/supplyCard.html',
		link: function(scope, elm, attrs) {
			console.log(scope.card);
		}
	};
});