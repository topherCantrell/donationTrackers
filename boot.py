import board
import digitalio
import storage

# Only one device can write to the disk at a time. Either the PC can write
# new code or the program can write the current value to the disk. This 
# file runs at boot time and determines who can write. Place a jumper
# from GP0 to GND to allow the PC to write. Remove the jumper to allow
# the program to write.

switch = digitalio.DigitalInOut(board.GP0)
switch.direction = digitalio.Direction.INPUT
switch.pull = digitalio.Pull.UP

value = switch.value
print("Readonly:", value)

# If there is a wire jumper from GP0 to GND, then the board will boot
# to allow the PC to write (for programming) 
storage.remount("/", readonly=not value)
