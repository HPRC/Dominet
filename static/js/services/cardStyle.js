clientModule.factory('cardStyle', function(){
	return {
		getButtonStyle: function(card){
			var colorDict = {
				"Treasure": "btn btn-warning",
				"Victory": "btn btn-success",
				"Action|Attack": "btn btn-danger",
				"Action|Reaction": "btn btn-info"
			};

			if (card.type in colorDict){
				return colorDict[card.type];
			} else {
				return "btn btn-default";
			}
		}
	};
});
