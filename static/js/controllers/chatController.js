clientModule.controller("chatController", function($rootScope, $scope, socket){
    $scope.inputText = "";

	$("#sendChat").click(function(){
		$scope.inputText = $scope.inputText.replace(/</g, "&lt;").replace(/>/g, "&gt;");
		socket.send(JSON.stringify({"command": "chat", "msg": $scope.inputText}));
		$("#inputChat").val("");
	});

	$("#inputChat").keypress(function(e){
		if(e.which==13){
			$scope.inputText = $scope.inputText.replace(/</g, "&lt;").replace(/>/g, "&gt;");
			socket.send(JSON.stringify({"command": "chat", "msg": $scope.inputText}))
			$("#inputChat").val("");
		}
	});

	$rootScope.$on("socketmsg", function(data, event){
		var jsonres = JSON.parse(event.data);
		if (jsonres.command === "chat"){
			if (jsonres.speaker){
				$("#gameChat").append("<br><b>" + jsonres.speaker + ": </b>" + jsonres.msg);
			} else {
				$("#gameChat").append("<br>" + jsonres.msg);
			}
			$(".scrollChat").scrollTop($(".scrollChat")[0].scrollHeight);
		}
	});

});
