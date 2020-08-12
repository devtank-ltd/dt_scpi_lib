install:
	# installs the udev rules and retriggers them
	cp udev.rules /etc/udev/rules.d/53-usbtmc.rules
	udevadm control --reload-rules
	udevadm trigger
