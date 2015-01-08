function validateUsername(){
	if ($("#inputUsername").val().indexOf(" ") != -1){
		$("#errorMsg").text("Name cannot have spaces");
		return false;
	} else if ($("#inputUsername").val().length > 25){
		$("#errorMsg").text("Name cannot be over 24 characters");
		return false;
	} else {
		return true;
	}
}