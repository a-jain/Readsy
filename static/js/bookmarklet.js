

href='javascript:void((function(){var a=location.href.replace(/^http%5C:%5C/%5C/(.*)$/,"$1");location.href="http://www.readsy.co/web?url="+escape(a);})())'

onclick="alert('Drag this link onto your toolbar to add the Readsy bookmarklet');return false"

  var t = '';
  if(window.getSelection){
    t = window.getSelection();
  }else if(document.getSelection){
    t = document.getSelection();
  }else if(document.selection){
    t = document.selection.createRange().text;
  }
  return t;

  javascript:void(
  	(function() {
  		var a=location.href.replace(/^http%5C:%5C/%5C/(.*)$/,"$1");
  		location.href="http://www.readsy.co/web?url="+escape(a);
  	})
  	()
  )