clientModule.factory('client', function(socket, favicon) {
	var constructor = function() {
		this.id = null;
		this.name = null;
		var that = this;

		//socket
		this.onmessage = function(event){
			var jsonres = JSON.parse(event.data);
			var exec = that[jsonres.command];
			if (exec != undefined){
				exec.call(that,jsonres);
			}
		};
	};

	constructor.prototype.init = function(json) {
			this.id = json.id;
			this.name = json.name;
	};

	constructor.prototype.initGameProperties = function(){
		this.turn = false;
		this.hand = [];
		this.kingdom = {};
		this.baseSupply = {};
		this.gameTrash = "";
		this.actions = 0;
		this.buys = 0;
		this.balance = 0;
		this.played = [];
		this.spendableMoney = 0;
		this.deckSize = 5;
		this.discardSize = 0;
		//mode overidden by turn
		this.modeJson = {"mode":"action"}; //.mode = action, buy, select, gain, wait, gameover
		this.priceModifier = {};
		this.gameLogs = "";

	};

	constructor.prototype.updateHand = function(json){
		this.hand = json.hand;
		this.updateSpendable();
	};

	constructor.prototype.announce = function(json){
		var msg = document.getElementById("msg");
		this.gameLogs += "<br>" + json.msg;
	};

	constructor.prototype.kingdomCards = function(json){
		var kingdomArray = JSON.parse(json.data);
		for (var i=0; i< kingdomArray.length; i++) {
			this.kingdom[kingdomArray[i].title] = kingdomArray[i];		
		}
	};

	constructor.prototype.baseCards = function(json){
		var baseArray = JSON.parse(json.data);
		for (var i=0; i< baseArray.length; i++) {
			this.baseSupply[baseArray[i].title] = baseArray[i];
		}
	};

	constructor.prototype.startTurn = function(json){
		this.turn = true;
		this.updateResources(json);
		this.spendableMoney = 0;
		this.updateSpendable();
		favicon.alertFavicon();
	};

	constructor.prototype.updateMode = function(json){
		this.modeJson = json;
		if (this.modeJson.mode === "selectSupply" || this.modeJson.mode === "select"){
			favicon.alertFavicon();
		}
	};

	constructor.prototype.endTurn = function(){
		if (!this.turn){
			return;
		}
		this.turn = false;
		this.discard(this.hand);
		this.played = []; //discarded on backend
		favicon.stopAlert();
		socket.send(JSON.stringify({"command": "endTurn"}));
	};

	constructor.prototype.discard = function(cards){
		if (cards.length == 0){
			return;
		}
		var cardsByTitle = cards.map(function(val){
			return val.title;
		});
		socket.send(JSON.stringify({"command": "discard", "cards": cardsByTitle}));
		//remove from hand
		for (var j=0; j<cards.length; j++){
			for (var i=0; i<this.hand.length; i++){
				if (cards[j] == this.hand[i]){
					this.hand.splice(i,1);
					i--;
				}
			}
		}
	};

	constructor.prototype.updateSpendable = function (){
		this.spendableMoney = 0;
		for (var i=0; i<this.hand.length; i++){
			if (this.hand[i].type.indexOf("Treasure") > -1 && this.hand[i].spend_all === true){
				this.spendableMoney += this.hand[i].value;
			}
		}
	};

	constructor.prototype.spendAllMoney = function(){
		if (this.modeJson.mode === "buy" && this.modeJson.bought_cards === true){
			return;
		}
		this.spendableMoney = 0;
		socket.send(JSON.stringify({"command": "spendAllMoney"}));
	};

	constructor.prototype.playCard = function(card){

		if (this.actions > 0 || card.type.indexOf("Action") === -1){
			this.actions -=1;
			socket.send(JSON.stringify({"command":"play", "card": card.title}));
			this.played.push(card);
			//remove from hand
			for (var i=0; i<this.hand.length; i++){
				if (card == this.hand[i]){
					this.hand.splice(i,1);
					i--;
				}
			}
		}

		if (card.type === "Treasure"){
			this.updateSpendable();
		}

	};

	constructor.prototype.buyCard = function(card){
		if (this.balance >= card.price + this.priceModifier[card.title]){
			this.buys -= 1;
			if (card.price + this.priceModifier[card.title] > 0){
				this.balance -= card.price + this.priceModifier[card.title];
			}
			socket.send(JSON.stringify({"command":"buyCard", "card": card.title}));
		}
	};

	constructor.prototype.updateAllPrices = function(json){
		this.priceModifier = json.modifier;
	};

	constructor.prototype.updatePiles = function(json){
		if (json.card in this.kingdom){
			this.kingdom[json.card].count = json.count;
		} else {
			this.baseSupply[json.card].count = json.count;
		}
	};

	constructor.prototype.updateResources = function(json){
		this.actions = json.actions;
		this.buys = json.buys;
		this.balance = json.balance;
		if (this.modeJson.mode === "buy" && this.buys === 0){
			this.endTurn();
		}
	};

	constructor.prototype.updateDeckSize = function(json){
		this.deckSize = json.size;
	};

	constructor.prototype.updateDiscardSize = function(json){
		this.discardSize = json.size;
	};

	constructor.prototype.updateTrash = function(json){
		this.gameTrash = json.trash;
	};

	constructor.prototype.getHand = function(){
		return this.hand;
	};

	constructor.prototype.getTurn = function(){
		return this.turn;
	};

	constructor.prototype.getActions = function(){
		return this.actions;
	};

	constructor.prototype.getBalance = function(){
		return this.balance;
	};

	constructor.prototype.getBuys = function(){
		return this.buys;
	};

	constructor.prototype.getKingdom = function(){
		return this.kingdom;
	};
	
	constructor.prototype.getBaseSupply = function(){
		return this.baseSupply;
	};

	constructor.prototype.getSpendableMoney = function(){
		return this.spendableMoney;
	};

	constructor.prototype.getModeJson = function(){
		return this.modeJson;
	};

	constructor.prototype.getName = function(){
		return this.name;
	};

	constructor.prototype.getName = function(){
		return this.name;
	};

	constructor.prototype.getDeckSize = function(){
		return this.deckSize;
	};

	constructor.prototype.getDiscardSize = function(){
		return this.discardSize;
	};

	constructor.prototype.getGameTrash = function(){
		return this.gameTrash;
	};

	constructor.prototype.getPriceModifier = function(){
		return this.priceModifier;
	};

	constructor.prototype.getGameLogs = function(){
		return this.gameLogs;
	};


	return new constructor();
});


