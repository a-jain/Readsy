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
        $("#progressbar").hide("fast", "linear");
    }
    
    function fillTextClick() {
    	var testText = "Just as she said this, she noticed that one of the trees had a door leading right into it. 'That's very curious!' she thought. 'But everything's curious today. I think I may as well go in at once.' And in she went.";    		
    	$("#inputText").focus();
    	var text = $("#inputText").val(); 
    	$("#inputText").val(text + (text != "" ? "\n" : "") + testText);  
    }

	function onStartSpritzClick(event) {
		var text = $('#inputText').val();
		var locale = "en_us;";
		
		$("#progressbar").fadeIn("fast");
		
		// Send to SpritzEngine to translate
		SpritzClient.spritzify(text, locale, onSpritzifySuccess, onSpritzifyError);
	};

	function onSpeedChange(event, speed) {
		$.cookie('spritz_speed', speed, { expires: 28, path: '/' });
	}

	// Display "Completed X of XXX"
	function showProgress(completed, total) {
	     $("#wordNumber").text(completed);
	     $("#wordTotal").text(total);
	};
	
	// Customized options
	var customOptions = {
			"redicleWidth" : 	434,	// Specify Redicle width
			"redicleHeight" : 	135,	// Specify Redicle height
			"defaultSpeed" :    300,
			"speedItems" :      [50, 100, 150, 200, 250, 300, 400, 500, 600, 900],
			"controlTitles" : {
            "pause" :         "Pause",
            "play" :          "Play",
            "back" :          "Previous Sentence"
        }
			
	};

	if (document.documentElement.clientWidth <= 480) {
		customOptions["redicleWidth"] = 302;
	}

	if (document.documentElement.clientWidth > 600) {
		$(document).ready(function() {
			$('#inputText').tooltip();
		});
	}

	var cookieVal = $.cookie('spritz_speed');
	if (cookieVal !== undefined) {
		// cast to int first
		customOptions['defaultSpeed'] = cookieVal;
	}

	var init = function() {
		var container = $("#spritzer");
		$("#clear").on("click", clearTextClick);
		$("#fill").on("click", fillTextClick);
		$("#startSpritz").on("click", onStartSpritzClick);			
		 
 		// Construct a SpritzController passing the customization options
 		spritzController = new SPRITZ.spritzinc.SpritzerController(customOptions);
 		spritzController.setProgressReporter(showProgress);
 		
 		// Attach the controller's container to this page's "spritzer" container
 		spritzController.attach(container);
 		container.on("onSpritzSpeedChange", onSpeedChange);
	};
	
	
	$(document).ready(function() {
		init();
	});

})();

function jDecode(str) {
	return $("<div/>").html(str.trim()).text();
}
