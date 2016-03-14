clientModule.factory('cardStyle', function(){
	return {
		getButtonStyle: function(card){
			var colorDict = {
				"Treasure": "card-treasure",
				"Victory": "card-victory",
				"Curse": "card-curse",
				"Action|Attack": "card-attack",
				"Action|Reaction": "card-reaction",
				"Action|Victory": "card-action-victory",
				"Treasure|Victory": "card-treasure-victory"
			};

			if (card !== null && card.type in colorDict){
				return colorDict[card.type];
			} else {
				return "card-action";
			}
		}
	};
});
