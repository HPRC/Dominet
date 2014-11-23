var client = {

	init: function() {
		//create client on server
		$.ajax({
			url: "/",
			type:'POST',
			success: function(data){
				alert("my id is : " + data);
			}
		});

	},

	saysomething: function(){
		alert("something");
	}

};

$(document).ready(function(){
	client.init();
});