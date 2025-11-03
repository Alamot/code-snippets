.PHONY: clean, .force-rebuild
all: kernel8.img

kernel8.img: boot.S uart.S .force-rebuild
	aarch64-linux-gnu-as -o boot.o boot.S 
	aarch64-linux-gnu-as -o uart.o uart.S 
	aarch64-linux-gnu-ld -T linker.ld -o kernel.elf boot.o uart.o 
	aarch64-linux-gnu-objcopy -O binary kernel.elf kernel8.img	

clean:
	rm *.o
	rm *.elf
	rm *.img
