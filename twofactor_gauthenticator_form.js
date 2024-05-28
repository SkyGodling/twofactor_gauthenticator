if (window.rcmail) {
  rcmail.addEventListener('init', function() {
	// remove the user/password/... input from login
    $('form > table > tbody > tr').each(function(){
    	$(this).remove();
    });
	
    // change task & action
    $('form').attr('action', './');
    $('input[name=_task]').attr('value', 'mail');
    $('input[name=_action]').attr('value', '');

	//determine twofactor field type based on config settings
	if(rcmail.env.twofactor_formfield_as_password)
		var twoFactorCodeFieldType = 'password';
	else
		var twoFactorCodeFieldType = 'text';
	
	//twofactor input form
    var text = '';
    text += '<tr>';
    text += '<td class="title"><label for="2FA_code"><strong>'+rcmail.gettext('two_step_verification_form', 'twofactor_gauthenticator')+'</strong></label></td>';
    text += '<td class="input"><input class="form-control" name="_code_2FA" id="2FA_code" size="10" maxlength="10" autocapitalize="off" autocomplete="off" type="' + twoFactorCodeFieldType + '" maxlength="10"></td>';
    text += '</tr>';

    if(rcmail.env.allow_save_device) {
        var remember_device_msg = rcmail.gettext('dont_ask_me_days', 'twofactor_gauthenticator');
        proceed_msg = rcmail.gettext('proceed', 'twofactor_gauthenticator');
        remember_device_msg = remember_device_msg.replace('{DAYS}', rcmail.env.days_to_remember_device);
		    text += '<tr>';
		    text += '<td class="title" colspan="2"><br /><label for="remember_2FA"><input type="checkbox" id="remember_2FA" name="_remember_2FA" value="yes" /> ' + remember_device_msg + '</label><hr /></td>';
		    text += '</tr>';
	} else {
        text += '<tr>';
        text += '<td class="title" colspan="2"><hr /></td>';
        text += '</tr>';
    }

    // create textbox
    $('form > table > tbody:last').append(text);
    $('#rcmloginsubmit').html(proceed_msg);

    $('#2FA_code').focus();
    
  });

};
