clientModule.controller("reorderController", function($scope, socket, client){
	$(".reorder-ul").sortable();
	$(".reorder-ul").disableSelection();

	$scope.doneReorder = function(){
		var ordered = $(".reorder-ul").sortable("toArray");
		//remove the done button from array
		ordered.splice(-1, 1);
		client.updateMode({"mode":"wait"});
		socket.send(JSON.stringify({"command": "reorder", "ordering": ordered}));
	};
});
