Function of this script is to download unifi firmware files from Ubiquity oficial firmware repository to your private one.
It uses their firmware definition file firmware.json to get URLs of firmwares, then it transforms those URLs to another ones which could be usable on your private web server and in the end the script downloads all wanted firmwares into your system.
The motivation for making this tool was the missing proxy setting in Unifi controller software which prevents upgrading of firmwares in networks where isn't direct access to the internet for unifi devices and unifi controller as well.

Usage:
- you need default installation of python3
- this works with unifi controller 6.x (tested only on 6.0.45)
- you need Unifi original firmware.json file (I was not able to find proper URL of this file at Ubiquity yet). It is reguraly updated by controller from Ubiquity server, so if you have another unifi controller in internet or the cloudkey in the internet, you can find this file in the root directory of the unifi service (typicaly /var/lib/unifi).
- make proper configuration of the script run in .yml config file (description of the items are inside of the sample config file)
- run the script
- expected output:
* new generated firmware.json file with modified URLs of the firmware files
* downloaded firmware files into the defined directory

- what next with this?
: replace new firmware.json file in the unifi controller without internet access
: restart unifi service
: since this time unfi controller will start present your new URLs of unifi firmware files to unifi devices

: place downloaded firmware files (whole dedicated directory) at some web server which is accessible from your unifi devices and properly setup the web server to match new modified URLs of firmware files
: since this time you will be able to upgrade firmwares in your whole unifi infrastructure without internet access

filtering:
You don't have to download all firmwares from Ubiquity server defined in firmware.json file. You can configure filters for controller versions and for unifi device models. Filter can be configured in .yml config file. So you can download only firmwares for your owned models which grealy lowers needed storage capacity.

using proxy:
For downloading of the firmware files you can configure proxy server in configuration .yml file. The proxy definition is compatible with using proxy in requests python module.
