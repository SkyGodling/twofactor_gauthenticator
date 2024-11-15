# twofactor_gauthenticator
This RoundCube plugin adds the Google 2-step verification to the login proccess (OTP)

## Add Vietnamese language support

2Steps verification
==========================

This RoundCube plugin adds the 2-step verification(OTP) to the login proccess.

It works with all TOTP applications [RFC 6238](https://www.rfc-editor.org/info/rfc6238)

Some code by:
[Ricardo Signes](https://github.com/rjbs)
[Justin Buchanan](https://github.com/jusbuc2k)
[Ricardo Iván Vieitez Parra](https://github.com/corrideat)

![2Steps](https://raw.github.com/skyalliance/twofactor_gauthenticator/master/screenshots/092443.png)

iRedMail_Reset_2FA
------------
I have added a Python GUI script to handle the issue of activation or deactivation when the phone is lost or the code is forgotten. With iRedMail_Reset_2FA folder.
![2Steps](https://raw.github.com/skyalliance/twofactor_gauthenticator/master/screenshots/2fa.jpg)
 
Installation
------------
- Clone from github:
    HOME_RC/plugins$ git clone [https://github.com/skyalliance/twofactor_gauthenticator.git](https://github.com/skyalliance/twofactor_gauthenticator.git)
    
- Activate the plugin into HOME_RC/config/config.inc.php:
    $config['plugins'] = array('twofactor_gauthenticator');


Configuration
-------------
Go to the Settings task and in the "2steps Google verification" menu, click 'Setup all fields (needs Save)'.

The plugin automatically creates the secret for you.

NOTE: plugin must be base32 valid characters ([A-Z][2-7]), see https://github.com/alexandregz/twofactor_gauthenticator/blob/master/PHPGangsta/GoogleAuthenticator.php#L18

From https://github.com/alexandregz/twofactor_gauthenticator/issues/139
To add accounts to the app, you can use the QR-Code (easy-way) or type the secret.
After checking the first code click 'Save'.

Get the default time from the server to synchronize with the Phone's NTP time.
----------------
To synchronize the time I added the following code in twofactor_gauthenticator.php
// Get the default time from the server to synchronize with the Phone's NTP time.
 date_default_timezone_set('Asia/Ho_Chi_Minh');
Change the time zone to suit your location

Enrollment Users
----------------
If config value *force_enrollment_users* is true, **ALL** users needs to login with 2-step method. They receive alert message about that, and they can't skip without save configuration


Samefield
---------
If config value *2step_codes_on_login_form* is true, 2-step codes (and recovery) must be sended with password value, append to this, from the login screen: "Normal" codes just following password (passswordCODE), recovery codes after two pipes (passsword||RECOVERYCODE)

Actually only into samefield branch


Codes
-----
Codes have a 2*30 seconds clock tolerance, like by default with Google app (Maybe editable in future versions)



License
-------
MIT, see License

Notes
-----
Tested with RoundCube 0.9.5 and Google app. Also with Roundcube 1.0.4

Remember, sync time it's essential for TOTP: "For this to work, the clocks of the user's device and the server need to be roughly synchronized (the server will typically accept one-time passwords generated from timestamps that differ by ±1 from the client's timestamp)" (from http://en.wikipedia.org/wiki/Time-based_One-time_Password_Algorithm)

Author
------
Alexandre Espinosa Menor <aemenor@gmail.com>

Issues
------
Open issues using github, don't send me emails about that, please -usually Gmail marks messages like SPAM

Testing
-------
- Vagrant: https://github.com/alexandregz/vagrant-twofactor_gauthenticator
- Docker: https://hub.docker.com/r/alexandregz/twofactor_gauthenticator/

Using with Kolab
----------------
Add a symlink into the public_html/assets directory

Show explained https://github.com/alexandregz/twofactor_gauthenticator/issues/29#issuecomment-156838186 by https://github.com/d7415

Client implementations
----------------------

You can use various [OTP clients](https://en.wikipedia.org/wiki/HMAC-based_One-time_Password_Algorithm#Applications) -link by https://github.com/helmo


Logs
----

Suggested by simon@magrin.com

To log errors with bad codes, change the $_enable_logs variable to true.
The logs are stored to the file HOME_RC/logs/log_errors_2FA.txt -directory must be created
Whitelist
---------

You can define whitelist IPs into config file (see config.inc.php.dist) to automatic login -the plugin don't ask you for code


Uninstall
---------

To deactivate the plugin, you can use two methods:

- To only one user: restore the user prefs from DB to null (rouncubeDB.users.preferences) -the user plugin options stored there.

- To all: remove the plugin from config.inc.php/remove the plugin itself


Activate only for specific users
--------------------------------

- Use config.inc.php file (see config.inc.php.dist example file)

- Modify array  **users_allowed_2FA** with users that you want to use plugin. NOTE: you can use regular expressions

## Use with 1.3.x version

Use *1.4.9-version* branch

## Security incident 2022-04-02

Reported by kototilt@haiiro.dev (thx for the report and the PoC script)

I made a little modification on script to not allow to save config without param session generated from a rendered page, to force user to introduce previously 2FA code and navigate across site.

NOTE: Also I check if user have 2FA activated because with only first condition -check SESSION- app kick out me before to activate 2FA.


#### `twofactor_gauthenticator_save()`

On function `twofactor_gauthenticator_save()` I added this code:

```php
    // save config
    function twofactor_gauthenticator_save() 
    {
        $rcmail = rcmail::get_instance();

		// 2022-04-03: Corrected security incidente reported by kototilt@haiiro.dev
		//					"2FA in twofactor_gauthenticator can be bypassed allowing an attacker to disable 2FA or change the TOTP secret."
		//
		// Solution: if user don't have session created by any rendered page, we kick out
		$config_2FA = self::__get2FAconfig();
		if(!$_SESSION['twofactor_gauthenticator_2FA_login'] && $config_2FA['activate']) {
			$this->__exitSession();
		}
```


The idea is to create a session variable from a rendered page, redirected from `__goingRoundcubeTask` function (redirector to `roundcube tasks`)


#### tests with PoC python script

Previously, with security compromised:

```bash
alex@vosjod:~/Desktop/report$ ./poc.py
Password:xxxxxxxx
1. Fetching login page (http://localhost:8888/roundcubemail-1.4.8)
2. Logging in
  POST http://localhost:8888/roundcubemail-1.4.8/?_task=login
3. Disabling 2FA
  POST http://localhost:8888/roundcubemail-1.4.8/?_task=settings&_action=plugin.twofactor_gauthenticator-save
  POST returned task "settings"
2FA disabled!
``` 

Modified code and tested again, not allowed to deactivated/modified without going to a RC task (with 2FA authentication):

```bash
alex@vosjod:~/Desktop/report$ ./poc.py
Password:xxxxxxxxx
1. Fetching login page (http://localhost:8888/roundcubemail-1.4.8)
2. Logging in
  POST http://localhost:8888/roundcubemail-1.4.8/?_task=login
3. Disabling 2FA
  POST http://localhost:8888/roundcubemail-1.4.8/?_task=settings&_action=plugin.twofactor_gauthenticator-save
  POST returned task "login"
Expected "settings" task, something went wrong
``` 



## docker-compose

You can use `docker-compose` file to modify and test plugin:

- Replace `mail.EXAMPLE.com` for your IMAP and SMTP server.
- `docker-compose up`
- You can use `adminer` to check DB and reset secrets, for example.
