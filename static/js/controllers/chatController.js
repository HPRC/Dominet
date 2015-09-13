clientModule.controller("chatController", function($rootScope, $scope, socket){
    $scope.inputText = "";
    $scope.messages = [];

	$scope.enterKey = function(e){
		if(e.which==13){
			$scope.enterChat();
		}
	};

	$scope.enterChat = function(){
		if ($scope.inputText.length > 0){
			socket.send(JSON.stringify({"command": "chat", "msg": $scope.inputText}))
			$scope.inputText = "";
		}
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
			var chat = document.getElementsByClassName("scrollChat")[0]
			chat.scrollTop = chat.scrollHeight;
		}
	});

});
