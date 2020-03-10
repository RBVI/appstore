$(function() {
    function display_unsupported_msg() {
	    CyMsgs.add_msg('Your browser is not supported. Consider switching to <a href="http://www.getfirefox.com">Firefox</a>.', 'error');
    }
    
    if (!$.support.ajax) {
        display_unsupported_msg();
    }

    if (navigator.appVersion.indexOf("Win") != -1) CyPlatform = "Windows";
    else if (navigator.appVersion.indexOf("Mac") != -1) CyPlatform = "macOS";
    else if (navigator.appVersion.indexOf("Linux") != -1) CyPlatform = "Linux";
    else CyPlatform = "";
});
