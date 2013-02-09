
default:
	@echo -n '$$ '
	cogs --default-name=world hello-with-configuration
	@echo -n '$$ '
	COGS_DEFAULT_NAME=world cogs hello-with-configuration
	@echo -n '$$ '
	echo "default-name: world" >cogs.conf
	@echo -n '$$ '
	cogs hello-with-configuration
	@echo -n '$$ '
	rm cogs.conf
	@echo -n '$$ '
	cogs help default-name

