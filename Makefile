install:
	# installs the udev rules and retriggers them
	cp *.rules /etc/udev/rules.d/
	udevadm control --reload-rules
	udevadm trigger
