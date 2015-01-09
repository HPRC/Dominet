clientModule.factory('cardStyle', function(){
	return {
		getButtonStyle: function(card){
			var colorDict = {
				"Money": "btn btn-warning",
				"Victory": "btn btn-success",
				"Action|Attack": "btn btn-danger"
			};

			if (card.type in colorDict){
				return colorDict[card.type];
			} else {
				return "btn btn-default";
			}
		}
	};
});
