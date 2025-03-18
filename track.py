import board
import busio
import neopixel
import digitalio
import time

import art_data

i2c = busio.I2C(board.GP17, board.GP16)
i2c.try_lock()

# i2c.scan()

ADDR = 114
i2c.writeto(ADDR, bytes([0x21]))  # 0010_xxx1 Turn the oscillator on
i2c.writeto(ADDR, bytes([239]))  # 1110_1111 Full brightness
i2c.writeto(ADDR, bytes([0b10000001]))  # 1000_x001 Blinking off, display on
# i2c.writeto(ADDR, bytes([0, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255, 255]))

neo = neopixel.NeoPixel(board.GP28, 25, auto_write=False)
neo.fill((0, 0, 0))
neo.show()

# Blue button
blue = digitalio.DigitalInOut(board.GP13)
blue.direction = digitalio.Direction.INPUT
blue.pull = digitalio.Pull.UP

# Yellow button
yellow = digitalio.DigitalInOut(board.GP14)
yellow.direction = digitalio.Direction.INPUT
yellow.pull = digitalio.Pull.UP

# Red button
red = digitalio.DigitalInOut(board.GP15)
red.direction = digitalio.Direction.INPUT
red.pull = digitalio.Pull.UP

mode = "boot"
previous_red = red.value
previous_blue = blue.value
previous_yellow = yellow.value

# 7-segment display patterns -- one row per digit
DIGITS = [
    0b00111111,
    0b00000110,
    0b01011011,
    0b01001111,
    0b01100110,
    0b01101101,
    0b01111101,
    0b00000111,
    0b01111111,
    0b01101111,
]

def display_value(digit, colon=False):
    """Display a 4-digit value on the 7-segment display."""
    digit = digit % 1_0000
    s = str(digit)
    while len(s)<4:
        s = ' ' + s    
    buf = []
    for c in s:
        if c == ' ':
            # Leading spaces
            buf.append(0)
        else:
            buf.append(DIGITS[int(c)])
    n = 255 if colon else 0
    i2c.writeto(ADDR, bytes([0, buf[0], 0, buf[1], 0, n, 0, buf[2], 0, buf[3], 0, 0, 0, 0, 0, 0, 0]))

def read_current_value():
    """Read the current value from the disk."""
    try:
        with open('/current_value.txt', 'r') as f:
            g = f.readline().strip()        
            return int(g)
    except:
        print(">> ignoring read error")
        return 0

def write_current_value(value):
    """Write the current value to the disk."""
    try:
        with open('/current_value.txt', 'w') as f:
            f.write(str(value))
    except:
        print(">> ignoring write error")

def draw_frame(pixels, color_replace={}):    
    """Draw a 'movie' frame on the NeoPixels."""
    for i in range(25):
        col = pixels[i]
        col = color_replace.get(col, col)                  
        neo[i] = COLORS[col]
    neo.show()

def draw_next_frame(state):
    """Draw the next frame of the currently playing 'movie'."""
    global movie_ended
        
    # Current state
    movie_data = state[0]
    ptr = state[1]    
    color_replace = state[3]

    # Count down the frame time
    if state[2] > 0:
        state[2] -= 1
        return 
    
    # Move to the next frame
    ptr += 2    
    if ptr >= len(movie_data):
        # End of the movie. Reset to idle and set the flag
        init_movie(art_data.MOVIE_IDLE)        
        movie_ended = True       
        return
    
    # Draw the next frame and start the counter
    state[1] = ptr
    state[2] = movie_data[ptr+1]    
    draw_frame(movie_data[ptr], color_replace)    

def init_movie(movie_data, color_replace={}):
    """Start playing a specific 'movie'."""
    global movie_state, movie_ended
    movie_state = [movie_data,-2,0, color_replace]
    movie_ended = False


# Show the current value
value = read_current_value()
display_value(value)

# Animation 'movies':
# idle = continuous no button
# red, blue, yellow = button pressed
# splash = after a button animation

COLORS = [
    (0, 0, 0),       # 0=black
    (100, 0, 0),     # 1=red
    (0, 100, 0),     # 2=green
    (0, 0, 100),     # 3=blue    
    (100, 100, 0),   # 4=yellow
    (100, 0, 100),   # 5=magenta
    (0, 100, 100),   # 6=cyan
    (100, 100, 100), # 7=white
    #
    (10,0,10), # 8..17 shades of 
    (20,0,20), # 9
    (30,0,30), # A
    (40,0,40), # B
    (50,0,50), # C
    (60,0,60), # D
    (70,0,70), # E
    (80,0,80), # F
    (90,0,90), # G
    (100,0,100),# H    
]

movie_state = None
movie_ended = False

# Start with the idle movie
init_movie(art_data.MOVIE_IDLE)

while True:

    # Read the buttons
    r,b,y = not red.value, not blue.value, not yellow.value

    # Adjust the value and mode with 0 to 1 transitions
    if r and not previous_red:
        value -= 1
        if value < 0:
            value = 0
        display_value(value)
        write_current_value(value)        
        init_movie(art_data.BUTTON_RED)
    elif b and not previous_blue:
        value += 5
        display_value(value)
        write_current_value(value)        
        init_movie(art_data.BUTTON_BLUE_YELLOW,{1:3})
    elif y and not previous_yellow:
        value += 1
        display_value(value)
        write_current_value(value)        
        init_movie(art_data.BUTTON_BLUE_YELLOW,{1:4})
    
    # New current button values
    previous_red = r
    previous_blue = b
    previous_yellow = y

    # Draw the next animation frame
    draw_next_frame(movie_state)

    time.sleep(0.01)
