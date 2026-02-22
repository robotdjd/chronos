to install:

For Debian/Ubuntu:

	sudo rm /var/lib/dpkg/lock-frontend
	sudo rm /var/cache/apt/archives/lock
	sudo dpkg --configure -a
	sudo apt update
	sudo apt install python3 python3-pip -y
	sudo apt update
	sudo apt install python3 python3-pip -y
	sudo apt-get install samba
	wget https://raw.githubusercontent.com/robotdjd/chronos/main/Chronos_installer.py
	sudo python3 Chronos_installer.py

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
