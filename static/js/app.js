// spritz
(function() {
	var spritzController = null;

	var onSpritzifySuccess = function(spritzText) {
		spritzController.startSpritzing(spritzText);
	};
	
	var onSpritzifyError = function(error) {
		alert("Unable to Spritz: " + error.message);
	};
	
    function clearTextClick() {
        $("#inputText").val("");
    }
    
    function fillTextClick() {
    	var testText = "Here's To The Crazy Ones. The misfits. The rebels. The trouble-makers. The round pegs in the square holes. The ones who see things differently. They're not fond of rules, and they have no respect for the status-quo. You can quote them, disagree with them, glorify, or vilify them. About the only thing you can't do is ignore them. Because they change things. They push the human race forward. And while some may see them as the crazy ones, we see genius. Because the people who are crazy enough to think they can change the world - are the ones who do.";    		
    	var text = $("#inputText").val();   	
        $("#inputText").val(text + (text != "" ? "\n" : "") + testText);
    }

	function onStartSpritzClick(event) {
		var text = $('#inputText').val();
		var locale = "en_us;";
		
		// Send to SpritzEngine to translate
		SpritzClient.spritzify(text, locale, onSpritzifySuccess, onSpritzifyError);
	};
	
	
	// Customized options
	var customOptions = {
			"redicleWidth" : 	434,	// Specify Redicle width
			"redicleHeight" : 	150,	// Specify Redicle height
			"defaultSpeed" : 500,
			"speedItems" : [200, 300, 400, 500, 600, 750] 
			
	};

	if (document.documentElement.clientWidth <= 500)
		customOptions["redicleWidth"] = 420;

	var init = function() {
		
		$("#clear").on("click", clearTextClick);
		$("#fill").on("click", fillTextClick);
		$("#startSpritz").on("click", onStartSpritzClick);			
		 
 		// Construct a SpritzController passing the customization options
 		spritzController = new SPRITZ.spritzinc.SpritzerController(customOptions);
 		
 		// Attach the controller's container to this page's "spritzer" container
 		spritzController.attach($("#spritzer"));
	};
	
	
	$(document).ready(function() {
		init();
	});

})();

//// redirects
// About button
$(document).ready(function() {
	navbarlinks();
});

function navbarlinks()
{
	$("#navbar1").click(function()
	{
	    if (!$("#jumbotron").is(":visible"))
	    {
	    	$("#aboutme").hide("fast", "linear", showjumbo());
	    	$("#contactme").hide("fast", "linear", showjumbo());
		    $("#list1").prop("class", "active");
		    $("#list2").prop("class", "inactive");
		    $("#list3").prop("class", "inactive");
		    navbarlinks();
	    }
	});

	$("#navbar2").click(function()
	{
	    if (!$("#aboutme").is(":visible"))
	    {
	    	$("#jumbotron").hide("fast", "linear", showabout());
	    	$("#contactme").hide("fast", "linear", showabout());
		    $("#list1").prop("class", "inactive");
		    $("#list2").prop("class", "active");
		    $("#list3").prop("class", "inactive");
		    navbarlinks();
	    }
	});

	$("#navbar3").click(function()
	{
	    if (!$("#contactme").is(":visible"))
	    {
	    	$("#jumbotron").hide("fast", "linear", showcontact());
	    	$("#aboutme").hide("fast", "linear", showcontact());
		    $("#list1").prop("class", "inactive");
		    $("#list2").prop("class", "inactive");
		    $("#list3").prop("class", "active");
		    navbarlinks();
	    }
	});
}

function showjumbo() {
	$("#jumbotron").fadeIn("fast");
}
function showabout() {
	$("#aboutme").fadeIn("fast");
}
function showcontact() {
	$("#contactme").fadeIn("fast");
}