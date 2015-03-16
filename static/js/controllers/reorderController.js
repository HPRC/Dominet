clientModule.controller("reorderController", function($scope, socket){
	$(".reorder-ul").sortable();
	$(".reorder-ul").disableSelection();

	$scope.doneReorder = function(){
		var ordered = $(".reorder-ul").sortable("toArray");
		//remove the done button from array
		ordered.splice(-1, 1);
		socket.send(JSON.stringify({"command": "reorder", "ordering": ordered}));
	};
});
