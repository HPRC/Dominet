clientModule.controller("lobbyController", function($rootScope, $scope){
	$scope.lobbyList = [];
	$rootScope.$on("socketmsg", function(data, event){
		var jsonres = JSON.parse(event.data);
		if (jsonres.command === "lobby"){
			$scope.$apply(function(){
				$scope.lobbyList = jsonres.lobby_list;
			});
		}
	});
});