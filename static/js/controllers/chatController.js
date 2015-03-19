clientModule.controller("chatController", function($rootScope, $scope, socket){
    $scope.inputText = "";
    $scope.messages = [];

	$("#inputChat").keypress(function(e){
		if(e.which==13){
			$scope.enterChat();
		}
	});

	$scope.enterChat = function(){
		socket.send(JSON.stringify({"command": "chat", "msg": $scope.inputText}))
		$("#inputChat").val("");	
		$scope.inputText = "";
	};

	$scope.$on("$destroy", function(){
		socketlistener();
	});
	var socketlistener = $rootScope.$on("socketmsg", function(data, event){
		var jsonres = JSON.parse(event.data);
		if (jsonres.command === "chat"){
			if (jsonres.speaker){
				$scope.$apply(function(){
					$scope.messages.push({
						speaker: jsonres.speaker,
						msg: " " + jsonres.msg
					});
				});
			} else {
				$scope.$apply(function(){
					$scope.messages.push({
						speaker: "",
						msg: jsonres.msg
					});
				});
			}
			$(".scrollChat").scrollTop($(".scrollChat")[0].scrollHeight);
		}
	});

});
