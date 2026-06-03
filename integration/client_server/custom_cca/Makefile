obj-m += my_cca.o

KDIR := /lib/modules/$(shell uname -r)/build
MODULE_DIR := $(CURDIR)

all:
	$(MAKE) -C $(KDIR) M=$(MODULE_DIR) modules

clean:
	$(MAKE) -C $(KDIR) M=$(MODULE_DIR) clean
