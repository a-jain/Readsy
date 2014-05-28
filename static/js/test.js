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
		var ironmanText = "The Iron Man came to the top of the cliff. How far had he walked? Nobody knows. Where did he come from? Nobody knows. How was he made? Nobody knows. Taller than a house, the Iron Man stood at the top of the cliff, on the very brink, in the darkness. The wind sang through his iron fingers. His great iron head, shaped like a dustbin but as big as a bedroom, slowly turned to the right, slowly turned to the left. His iron ears turned, this way, that way. He was hearing the sea. His eyes, like headlamps, glowed white, then red, then infrared, searching the sea. Never before had the Iron Man seen the sea. He swayed in the strong wind that pressed against his back. He swayed forward, on the brink of the high cliff. And his right foot, his enormous iron right foot, lifted - up, out into space, and the Iron Man stepped forward, off the cliff, into nothingness. CRASH! Down the cliff the Iron Man came toppling, head over heels. CRASH! CRASH! CRASH! From rock to rock, snag to snag, tumbling slowly. And as he crashed and crashed and crashed. His iron legs fell off. His iron arms broke off, and the hands broke off the arms. His great iron ears fell off and his eyes fell out. His great iron head fell off. All the separate pieces tumbled, scattered, crashing, bumping, clanging, down on to the rocky beach far below. A few rocks tumbled with him. Then. Silence. Only the sound of the sea, chewing away at the edge of the rocky beach, where the bits and pieces of the Iron Man lay scattered far and wide, silent and unmoving. Only one of the iron hands, lying beside an old, sand-logged washed-up seaman’s boot, waved its fingers for a minute, like a crab on its back. Then it lay still. While the stars went on wheeling through the sky and the wind went on tugging at the grass on the cliff top and the sea went on boiling and booming. Nobody knew the Iron Man had fallen. Night passed. Just before dawn, as the darkness grew blue and the shapes of the rocks separated from each other, two seagulls flew crying  over the rocks. They landed on a patch of sand. They had two chicks in a nest on the cliff. Now they were searching for food. One of the seagulls flew up - Aaaaaark! He had seen something. He glided low over the sharp rocks. He landed and picked something up. Something shiny, round and hard. It was one of the Iron Man’s eyes. He brought it back to his mate. They both looked at this strange thing. And the eye looked at them. It rolled from side to side looking first at one gull, then at the other. The gulls, peering at it, thought it was a strange kind of clam, peeping at them from its shell.";
		var locale = "en_us;";
		var text = "Shouldn't see this";
		
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
		$("#textChooser").on("change", onTextSelected);  
		// init();
	});

})();

function onTextSelected(e) {
	// console.log("hi2");
	var option = $('option:selected', this); 
    var name = option.text();

    var url = option.val();
    // console.log("hi");
  	// console.log(url);  
    // $('#selectionTitle').text(name);
    $('#spritzer').data('controller').setUrl(url);

    $('#printButton').prop("href", url);
}


function jDecode(str) {
	return $("<div/>").html(str.trim()).text();
}
