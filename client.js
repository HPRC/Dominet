var client = (function() {

	var constructor = function() {
		this.id = null;
	};

	constructor.prototype = {
		init: function() {
			//create client on server
			$.ajax({
				url: "/",
				type:'POST',
				context:this,
				success: function(data){
					this.id = parseInt(data);
					this.waitServer();
				}
			});
			$("#msg").text("Waiting for other player...");
		},

		initGame: function(json){
			console.log("let the games begin" + json.player1 + " vs "+ json.player2);
			this.waitServer();
		},

		waitServer: function(){
			$.ajax({
				url: "/wait/" + this.id,
				context: this,
				success: function(data){
					console.log(data);
					var jsonres = JSON.parse(data);
					if (jsonres.command === "initgame"){
						this.initGame(jsonres);
					} else if (jsonres.command === "startturn" && jsonres.turn === this.id){
						this.startTurn(jsonres);
					} else if (jsonres.command === "announce"){
						$('#msg').append("<br>" + jsonres.msg);
						this.waitServer();
					}
				}
			});
		},

		startTurn: function(data){
			var that = this;
			$("#endTurn").click(function(){
				$.ajax({
					url: "/respond/" + that.id,
					type:'POST',
					dataType: "json",
					data: JSON.stringify({
						"id": data["id"],
						"action": "endturn"
					}),
					context:that,
					success: function(data){
						that.waitServer();
					}
				});
				$("#endTurn").css('visibility', 'hidden');
			});
			$("#endTurn").css('visibility', 'visible');
			this.waitServer();
		}
	};

	return constructor;

}());

$(document).ready(function(){
	var c = new client();
	c.init();
});