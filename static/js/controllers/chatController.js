clientModule.controller("chatController", function($scope, socket){
	$("#sendChat").click(function(){
		var msg = $("#inputChat").val();
		msg = msg.replace(/</g, "&lt;").replace(/>/g, "&gt;");
		socket.send(JSON.stringify({"command": "chat", "msg": msg}))
	});

	$("#inputChat").keypress(function(e){
		if(e.which==13){
			var msg = $("#inputChat").val();
			msg = msg.replace(/</g, "&lt;").replace(/>/g, "&gt;");
			socket.send(JSON.stringify({"command": "chat", "msg": msg}))
			$("#inputChat").val("");
		}
	});

	socket.onmessage = function(event){
		socket.onmessage(event);
		console.log("chat");
		var jsonres = JSON.parse(event.data);
		if (jsonres.command === "chat"){
			console.log("A");
			$("#gameChat").append("<br><b>" + jsonres.speaker + ": </b>" + jsonres.msg);
			$("#scrollChat").scrollTop($("#scrollChat")[0].scrollHeight);
		}
	};

});
