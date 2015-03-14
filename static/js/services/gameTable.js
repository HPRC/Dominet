clientModule.factory('gameTable', function(){
	/* object representing a game table 
		title = name of table
		seats = number of players
		required = list of card titles to require in generating game kingdom
	*/
	return {
		title:"", 
		seats:2, 
		required:[]
	};
});
