.PHONY: clean, .force-rebuild
all: bootloader.bin

bootloader.bin: os.asm .force-rebuild
	nasm -fbin os.asm -o os.bin

clean:
	rm *.bin
