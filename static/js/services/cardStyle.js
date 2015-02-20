clientModule.factory('cardStyle', function(){
	return {
		getButtonStyle: function(card){
			var colorDict = {
				"Treasure": "btn btn-warning",
				"Victory": "btn btn-success",
				"Curse": "btn btn-curse",
				"Action|Attack": "btn btn-danger",
				"Action|Reaction": "btn btn-info",
				"Action|Victory": "btn btn-default-success"
			};

			if (card.type in colorDict){
				return colorDict[card.type];
			} else {
				return "btn btn-default";
			}
		}
	};
});
