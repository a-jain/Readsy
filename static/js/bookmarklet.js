javascript:void(
	(function() {
		var t = '';
		if(window.getSelection){
			t = window.getSelection();
		}else if(document.getSelection){
			t = document.getSelection();
		}else if(document.selection){
			t = document.selection.createRange().text;
		}
		if (t == '') {
			var a=location.href.replace(/^http%5C:%5C/%5C/(.*)$/,"$1");
			location.href="http://www.readsy.co/web?url="+encodeURIComponent(a);
		} else {

			location.href="http://www.readsy.co/text/"+encodeURIComponent(t.replace("/", "%2F"));
		}
	})
	()
)

document.URL.split("/")[3]

javascript:void((function() {	var t = ''; if(window.getSelection){t = window.getSelection();}else if(document.getSelection){t = document.getSelection();}else if(document.selection){	t = document.selection.createRange().text;}	if (t == '') {var a=location.href.replace(/^http%5C:%5C/%5C/(.*)$/,"$1");location.href="http://www.readsy.co/web?url="+encodeURIComponent(a);} else {location.href="http://www.readsy.co/text/"+encodeURIComponent(t.replace("/", "%2F"));}})())