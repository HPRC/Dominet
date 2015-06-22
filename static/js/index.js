function validateUsername(){
	var name = document.getElementById("inputUsername").value;
	var errMsg = document.getElementById("errorMsg");
	if (name.indexOf(" ") !== -1){
		errMsg.innerHTML = "Name cannot have spaces";
		return false;
	} else if (name.length > 25){
		errMsg.innerHTML = "Name cannot be over 24 characters";
		return false;
	} else if (name.length < 1){
		errMsg.innerHTML = "Name cannot be empty";
		return false;
	} else {
		return true;
	}
}