
default:
	@echo -n '$$ '
	cogs write-hello
	@echo -n '$$ '
	cogs write-hello -o hello.txt
	@echo -n '$$ '
	cat hello.txt; rm hello.txt
	@echo -n '$$ '
	cogs write-hello --output=hello.txt world
	@echo -n '$$ '
	cat hello.txt; rm hello.txt
	@echo -n '$$ '
	cogs help write-hello

