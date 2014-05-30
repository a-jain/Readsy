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

    function onBtnSeekClick() {
    	var num = document.forms["seekForm"]["seekNum"].value;
    	$('#spritzer').data('controller').seek(num, 'absolute');
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
		$("#btnSeek").on("click", onBtnSeekClick);		
		 
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

// redirects
$(document).ready(function() {
	navbarlinks();

	if (document.URL.split("/")[3] == "text") {
		// window.history.replaceState("", "Readsy", "/");
		document.title = "Readsy";
	}

	// hash controller
	if(window.location.hash) {
  		var hash = window.location.hash.substring(1);
 		if (hash == "editor") {
  			$( "#navbar2" ).click();
  		}
  		if (hash == "about") {
  			$( "#navbar3" ).click();
  		}
  		if (hash == "contact") {
  			$( "#navbar4" ).click();
  		}
    }
});

function navbarlinks()
{
	var baseTitle = "Readsy"
	$("#navbar1").click(function()
	{
	    if (!$("#jumbotron").is(":visible"))
	    {
	    	$("#editor").hide("fast", "linear", showjumbo());
	    	$("#aboutme").hide("fast", "linear", showjumbo());
	    	$("#contactme").hide("fast", "linear", showjumbo());
	    	// console.log($("#editortitle").text());
	    	if (!$("#editortitle").text().slice(-1).match(/[\!\.\?]/) && $("#editortitle").text() !== "")
	    		$("#editortitle").append("\.");
	    	var temp = $("#editor").editable("getText")[0].trim();
	    	temp = temp.replace(/\s+/g, ' ');
	    	temp = temp.replace(/([a-z])([\.\!\?])(?=[a-zA-Z])/g, '$1$2 ');
	    	$("#inputText").val(temp);
		    $("#list1").prop("class", "active");
		    $("#list2").prop("class", "inactive");
		    $("#list3").prop("class", "inactive");
		    $("#list4").prop("class", "inactive");
		    document.title = baseTitle;
		    if (titleText != "")
			{
				document.title += " - " + fileName;
			}
		    navbarlinks();
	    }
	});

	$("#navbar2").click(function()
	{
	    if (!$("#editor").is(":visible"))
	    {
	    	$("#jumbotron").hide("fast", "linear", showeditor());
	    	$("#aboutme").hide("fast", "linear", showeditor());
	    	$("#contactme").hide("fast", "linear", showeditor());
		    $("#list1").prop("class", "inactive");
		    $("#list2").prop("class", "active");
		    $("#list3").prop("class", "inactive");
		    $("#list4").prop("class", "inactive");
		    document.title = baseTitle + " - Editor";
		    navbarlinks();
	    }
	});

	$("#navbar3").click(function()
	{
	    if (!$("#aboutme").is(":visible"))
	    {
	    	$("#jumbotron").hide("fast", "linear", showabout());
	    	$("#editor").hide("fast", "linear", showabout());
	    	$("#contactme").hide("fast", "linear", showabout());
		    $("#list1").prop("class", "inactive");
		    $("#list2").prop("class", "inactive");
		    $("#list3").prop("class", "active");
		    $("#list4").prop("class", "inactive");
		    document.title = baseTitle + " - About";
		    navbarlinks();
	    }
	});

	$("#navbar4").click(function()
	{
	    if (!$("#contactme").is(":visible"))
	    {
	    	$("#jumbotron").hide("fast", "linear", showcontact());
	    	$("#editor").hide("fast", "linear", showcontact());
	    	$("#aboutme").hide("fast", "linear", showcontact());
		    $("#list1").prop("class", "inactive");
		    $("#list2").prop("class", "inactive");
		    $("#list3").prop("class", "inactive");
		    $("#list4").prop("class", "active");
		    document.title = baseTitle + " - Contact";
		    navbarlinks();
	    }
	});
}

function showjumbo() {
	$("#jumbotron").fadeIn("fast");
}
function showeditor() {
	$("#editor").fadeIn("fast");
}
function showabout() {
	$("#aboutme").fadeIn("fast");
}
function showcontact() {
	$("#contactme").fadeIn("fast");
}

$(window).on('hashchange', function() {
    ga('send', 'pageview', { 'page': location.pathname + "#"  + location.hash.substr(1) });
});

function jDecode(str) {
	return $("<div/>").html(str.trim()).text();
}

function updateEditor() {
	var content = jDecode(formString);
	var contentsplit = content.split('\n\n')

	for (var i = 0; i < contentsplit.length; i++)
	{
		contentsplit[i] = contentsplit[i].trim();
		if (!contentsplit[i].slice(-1).match(/[\!\.\?]/) && contentsplit[i] !== "")
		{
			contentsplit[i] += "\.";
		}
		$("#editor").append("<p id=\"editorpara\">" + contentsplit[i] + "\n\n</p>" );
	}
}
