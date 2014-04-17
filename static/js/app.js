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
    	var testText = "Here's To The Crazy Ones. The misfits. The rebels. The trouble-makers. The round pegs in the square holes. The ones who see things differently. They're not fond of rules, and they have no respect for the status-quo. You can quote them, disagree with them, glorify, or vilify them. About the only thing you can't do is ignore them. Because they change things. They push the human race forward. And while some may see them as the crazy ones, we see genius. Because the people who are crazy enough to think they can change the world - are the ones who do";    		
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
			"speedItems" : [150, 200, 300, 400, 450, 500, 550, 600, 750] 
			
	};

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

