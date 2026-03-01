to install:

For Debian/Ubuntu:

	sudo rm /var/lib/dpkg/lock-frontend
	sudo rm /var/cache/apt/archives/lock
	sudo dpkg --configure -a
	sudo apt update
	sudo apt install python3 python3-pip -y
	sudo apt update
	sudo apt install python3 python3-pip -y
	sudo apt install python3-pexpect
	sudo apt-get install samba
	wget https://raw.githubusercontent.com/robotdjd/chronos/main/Chronos_installer.py
	sudo python3 Chronos_installer.py

if you are having problems installing or need to update run the updater:

	wget https://raw.githubusercontent.com/robotdjd/chronos/main/Chronos_updater.py
	sudo python3 Chronos_updater.py

backend connect:

backend connect will only work with Windows, MacOs, or non-headless versons of linux. (needs a gui)
use backend connect by opening it using a command line
backend connect allows you to add and remove files from your Chronos webpage and reboot it (smb and ssh)
note that it also allows you to access the core part of the server so be careful!!!
if you want to add files that are visable from the page make sure the files you add go into the folder "files"

commands

start:

	sudo /mnt/sda1/shared/dashboard.sh start

stop:

	sudo /mnt/sda1/shared/dashboard.sh stop

restart:

	sudo /mnt/sda1/shared/dashboard.sh reboot

helpful hidden pages

how to make custom pages:

	http://chronos.local/customhtmlpages

info page:

	http://chronos.local/info

toast

	http://chronos.local/toast


