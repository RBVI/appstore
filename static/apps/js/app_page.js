var AppPage = (function($) {
    /*
     ================================================================
       Install via Cytoscape 3 App Manager
     ================================================================
    */

    var AppManagerURL = 'https://127.0.0.1:2607/';

    function is_manager_running(callback) {
        $.ajax(AppManagerURL + 'status/',
            {'type': 'GET',
             'success': function() { callback(true); },
             'error': function() { callback(false); }});
    }
    
    function get_app_status(fullname, callback) {
        $.getJSON(AppManagerURL + 'status/' + fullname,
            {},
            callback);
    }

    function install_app(app_name, app_version, callback) {
        $.getJSON(AppManagerURL + 'install/' + app_name + '/' + app_version,
            {},
            callback);
    }

    var install_btn_last_class = [];

    function setup_install_btn(install_btn, btn_class, icon_class, btn_text, func) {
        var last_class = install_btn_last_class[install_btn];
        if (install_btn in install_btn_last_class) {
            install_btn.removeClass(install_btn_last_class[install_btn]);
            delete install_btn_last_class[install_btn];
        }
        install_btn.addClass(btn_class);
        install_btn_last_class.push(btn_class);

        install_btn.find('i').attr('class', '');
        install_btn.find('i').addClass(icon_class);

        install_btn.find('h4').html(btn_text);

        install_btn.off('click');
        install_btn.removeClass('disabled');
        if (func) {
            var license_modal = $('#license_modal');
            if (license_modal.size() !== 0) {
                license_modal.find('.btn-primary').click(function() {
                    license_modal.modal('hide');
                    func();
                });
                install_btn.click(function() {
                    var license_iframe = license_modal.find('iframe');
                    license_iframe.attr('src', license_iframe.attr('data-src'));
                    license_modal.modal('show');
                });
            } else {
                /* license modal doesn't exist in DOM */
                install_btn.click(func);
            }
        } else {
            install_btn.addClass('disabled');
        }
    }

    function set_install_btn_to_download(install_btn, release_url, app_filename) {
        var label;
        var app_platform = install_btn.attr("platform");
        var app_workswith = install_btn.attr("workswith");
        var newer_chimerax = is_chimerax && version_compatible(ua_version, "(>=1.2.dev202101280755)");
        if (newer_chimerax) {
            // make request for installable state of wheel
            wheel_name = app_filename.split("/").pop()
            var xhr = new XMLHttpRequest();
            xhr.open("GET", "installable:" + wheel_name);
            xhr.onreadystatechange = function () {
                if(xhr.readyState === XMLHttpRequest.DONE) {
                    var status = xhr.status;
                    if (status === 0 || (status >= 200 && status < 400)) {
                        // The request has been completed successfully
                        label = xhr.responseText;
                    } else {
                        // Oh no! There has been an error with the request!
                        label = "Download";
                    }
                    setup_install_btn(install_btn, 'btn-primary', 'icon-cy-install-download', label,
                                      function() {
                                          window.location.href = release_url;
                                      });
                }
            }
            xhr.send();
	    return;
        }
        var installable = is_chimerax && version_compatible(app_workswith);
        if (!app_platform) {
            if (installable)
                label = "Install";
            else
                label = "Download";
        }
        else {
            var my_platform = "";
            if (navigator.appVersion.indexOf("Win") != -1)
                my_platform = "Windows";
            else if (navigator.appVersion.indexOf("Mac") != -1)
                my_platform = "macOS";
            else if (navigator.appVersion.indexOf("Linux") != -1)
                my_platform = "Linux";
            installable = installable && app_platform == my_platform;
            if (installable)
                label = "Install";
            else
                label = '<div class="cy-app-install-label">'
                        + app_platform + "<br>Download</div>";
        }
        setup_install_btn(install_btn, 'btn-primary', 'icon-cy-install-download', label,
            function() {
                window.location.href = release_url;
            });
    }

    function set_install_btn_to_installing(install_btn) {
        setup_install_btn(install_btn, 'btn-info', 'icon-cy-install-install', 'Installing...');
    }

    function set_install_btn_to_install(install_btn, app_name, latest_release_version) {
        setup_install_btn(install_btn, 'btn-info', 'icon-cy-install-install', 'Install',
            function() {
                set_install_btn_to_installing(install_btn);
                install_app(app_name, latest_release_version, function(result) {
                    if (result['install_status'] === 'success') {
                        CyMsgs.add_msg(result['name'] + ' has been installed! Go to Cytoscape to use it.', 'success');
                        set_install_btn_to_installed();
                    } else {
                        CyMsgs.add_msg('Could not install &ldquo;' + result['name'] + '&rdquo; app: <tt>' + result['install_status'] + '</tt>', 'error');
                        set_install_btn_to_install(app_name, latest_release_version);
                    }
                });
            });
    }

    function set_install_btn_to_upgrading(install_btn) {
        setup_install_btn(install_btn, 'btn-warning', 'icon-cy-install-upgrade', 'Upgrading...');
    }

    function set_install_btn_to_upgrade(install_btn, app_name, latest_release_version) {
        setup_install_btn('btn-warning', 'icon-cy-install-upgrade', 'Upgrade',
            function() {
                set_install_btn_to_upgrading(install_btn);
                install_app(app_name, latest_release_version, function(result) {
                    if (result['install_status'] === 'success') {
                        CyMsgs.add_msg(result['name'] + ' has been updated! Go to Cytoscape to use it.', 'success');
                        set_install_btn_to_installed();
                    } else {
                        CyMsgs.add_msg('Could not update &ldquo;' + result['name'] + '&rdquo; app: <tt>' + result['install_status'] + '</tt>', 'error');
                        set_install_btn_to_install(app_name, latest_release_version);
                    }
                });
            });
    }

    function set_install_btn_to_installed(install_btn) {
        setup_install_btn(install_btn, 'btn-success', 'icon-cy-install-installed', 'Installed');
    }

    function setup_install(release_id, app_name, app_fullname, latest_release_url, latest_release_version, install_app_help_url, app_filename) {
        set_install_btn_to_download($('#'+release_id), latest_release_url, app_filename);

        /* Do not bother checking if ChimeraX is running
        is_manager_running(function(is_running) {
            if (is_running) {
                get_app_status(app_fullname, function(app_status) {
                    if (app_status.status === 'not-found' || app_status.status === 'uninstalled') {
                        set_install_btn_to_install(app_fullname, latest_release_version);
                    } else if (app_status.status === 'installed') {
                        var installed_version = app_status.version;

                        if (installed_version === latest_release_version) {
                            set_install_btn_to_installed();
                        } else {
                            set_install_btn_to_upgrade(app_fullname, latest_release_version);
                        }
                    }
                });
            } else {
                CyMsgs.add_msg('Want an easier way to install apps? <a href="' + install_app_help_url + '" target="_blank">Click here</a> to learn how!', 'info');
            }
        });
        */
    }

    function setup_cy_2x_download_popover(plugins_dir_img) {
        $('.cy-app-2x-download-popover').popover({
            'title': 'How to Install',
            'html': true,
            'content': '<p>Download to your <strong>plugins</strong> folder.</p><p align="center"><img style="margin-top: 1em;" src="' + plugins_dir_img + '"></p>',
            'placement': 'bottom',
            'trigger': 'hover',
        });
    }
    
    /*
     ================================================================
       Stars
     ================================================================
    */
    
    function rating_to_width_percent(rating) {
        return Math.ceil(100 * rating / 5);
    }

    function width_percent_to_rating(width_percent) {
        return Math.ceil(width_percent * 5 / 100);
    }

    function cursor_x_to_rating(cursor_x, stars_width) {
        var rating = 5 * cursor_x / stars_width;
        if (rating <= 0.5)
            return 0;
        else if (rating > 5.0)
            return 5;
        else
            return Math.ceil(rating);
    }

    function setup_rate_popover(popover) {
        var stars_tag      = $('.popover-content .rating-stars');
        var stars_full_tag = $('.popover-content .rating-stars-filled');
        var rating = 5;
        $('.popover-title .close').click(function() {
            popover.popover('toggle');
        });
        $('.popover-content .rating-stars').mousemove(function(e) {
            var potential_rating = cursor_x_to_rating(e.pageX - $(this).offset().left, $(this).width());
            var width_percent = rating_to_width_percent(potential_rating);
            stars_full_tag.css('width', width_percent + '%');
        }).click(function() {
            rating = width_percent_to_rating(parseInt(stars_full_tag.css('width')));
            $('.popover-content #rate-btn #rating').text(rating);
        }).mouseleave(function() {
            var width_percent = rating_to_width_percent(rating);
            stars_full_tag.css('width', width_percent + '%');
        });
        $('.popover-content #rate-btn').click(function() {
            $(this).text('Submitting...').attr('disabled', 'true');
            $.post('', {'action': 'rate', 'rating': rating}, function(data) {
                popover.off('click').popover('destroy').css('cursor', 'default');
                popover.find('.rating-stars-filled').css('width', data.stars_percentage.toString() + '%');
                $('#rating-count').text('(' + data.votes.toString() + ')');
                popover.tooltip({'title': 'Your rating has been submitted. Thanks!'}).tooltip('show');
                setTimeout(function() {
                    popover.tooltip('hide');
                }, 5000);
            });
        });
    }

    function setup_stars() {
        var stars_tag       = $('#app-usage-info .rating-stars');
        var stars_empty_tag = $('#app-usage-info .rating-stars-empty');
        var stars_full_tag  = $('#app-usage-info .rating-stars-filled');
        stars_tag.popover({
            'trigger': 'manual',
            'content': $('#rate-popover-content').html()
        }).click(function() {
            stars_tag.popover('toggle');
            setup_rate_popover($(this));
        });
        stars_empty_tag.click(stars_tag.click);
        stars_full_tag.click(stars_tag.click);
    }


    function setup_details() {
        MarkdownUtil.format($('#cy-app-details-md'));
    }
    
    /*
     ================================================================
       Release Notes
     ================================================================
    */
    
    function setup_release_notes() {
        $('.cy-app-release-notes').each(function() {
            MarkdownUtil.format($(this));
        });
        
        $('.timeago').timeago();
    }
    
    /*
     ================================================================
       Download Stats
     ================================================================
    */
    
    function setup_download_stats() {
        if (is_chimerax)
            $('#downloadstats').html("Download Stats requires Flash and is not available from ChimeraX");
    }
    
    /*
     ================================================================
       UserAgent and Version
     ================================================================
    */

    var useragent = "";
    var ua_version = "";
    var is_chimerax = false;

    (function(){
        var ua_string = navigator.userAgent.trim();
        var cx = ua_string.indexOf("UCSF-ChimeraX");
        if (cx == -1)
            useragent = ua_string;
        else {
            var slash = ua_string.indexOf("/", cx);
            if (slash == -1)
                useragent = ua_string
            else {
                useragent = ua_string.substring(cx, slash);
                var start = slash + 1;
                var end = start;
                while (end < ua_string.length) {
                    if (/\s/.test(ua_string[end]))
                        break;
                    end += 1;
                }
                ua_version = ua_string.substring(start, end);
                is_chimerax = true;
            }
        }
    })();

    function version_compatible(ua_version, needed) {
	var match = /\(([=<>~]+)(.+)\)/.exec(needed);
	if (!match)
	    return true;
	var operator = match[1];
	var needed_version = parse_version(match[2]);
	var have_version = parse_version(ua_version);
	return compare_version(operator, have_version, needed_version);
    }

    function parse_version(v) {
	// Returns list of 2 items:
	// [0] = array of Numbers for dotted version number at the front, and
	// [1] = string for trailing text
	// So "1.0rc1" -> [ [1, 0], "rc1" ]
	var match = /([0-9.]+)([^0-9.].*)/.exec(v);
	var base_version, trailer;
	if (!match) {
	    base_version = v;
	    trailer = null;
	} else {
	    base_version = match[1];
	    base_version = base_version.replace(/\.+$/, '');
	    trailer = match[2];
	}
	var va = base_version.split('.').map(Number);
	return [va, trailer];
    }

    var comp_ops = {
	'>=': function(cmp) { return cmp >= 0; },
	'<=': function(cmp) { return cmp <= 0; },
	'==': function(cmp) { return cmp == 0; },
	'>':  function(cmp) { return cmp > 0; },
	'<':  function(cmp) { return cmp < 0; },
    }

    function compare_version(op, have, want) {
	var have_version = have[0];
	var want_version = want[0];
	var comp_op = comp_ops[op];
	if (comp_op) {
	    var match_length = Math.min(have_version.length, want_version.length);
	    var cmp = 0;        // -1 = have<want, 0 = have==want, 1 = have>want
	    // Compare matching version parts
	    for (var i = 0; i < match_length; i++)
		if (have_version[i] < want_version[i]) {
		    cmp = -1;
		    break;
		} else if (have_version[i] > want_version[i]) {
		    cmp = 1;
		    break;
		}
	    // If matching base version parts compare equal, then
	    // the version with more parts if newer
	    if (cmp == 0) {
		if (have_version.length < want_version.length)
		    cmp = -1;
		else if (have_version.length > want_version.length)
		    cmp = 1;
		// If still equal, then newer trailer wins if both have trailers.
		// If not, assume that they are the same since we have either:
		// (a) want = 1.0b1 and have = 1.0 => release is newer, or
		// (b) want = 1.0 and have = 1.0b1 => release is being tested.
		else {
		    var have_trailer = have[1];
		    var want_trailer = want[1];
		    if (have_trailer && want_trailer) {
			if (have_trailer < want_trailer)
			    cmp = -1
			else if (have_trailer > want_trailer)
			    cmp = 1
		    }
		}
	    }
	    // Do the actual comparison
	    return comp_op(cmp);
	} else if (op == '~=') {
	    // TODO: compare trailer if need be
	    // TODO: ~= means the "want" version must match up to the last part,
	    // and the last "want" part must be less than the matching "have" part
	    var match_length = want_version.length - 1;
	    if (have_version.length <= match_length)
		// If "have" has fewer parts than "want", the existing parts either
		// (a) match and "want" is newer, or
		// (b) do not match and fail ~= semantics
		return false;
	    for (var i = 0; i < match_length; i++)
		if (have_version[i] != want_version[i])
		    return false;
	    return have_version[match_length] >= want_version[match_length];
	} else
	    return false;
    }

    /*
     ================================================================
       Init
     ================================================================
    */
    
    return {
        'setup_install': setup_install,
        'setup_cy_2x_download_popover': setup_cy_2x_download_popover,
        'setup_stars': setup_stars,
        'setup_details': setup_details,
        'setup_release_notes': setup_release_notes,
        'setup_download_stats': setup_download_stats,
    }
})($);
