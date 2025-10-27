import random
import string
import keyboard
import time

def random_8():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

print('Script started, press F8 to stop.')
while True:
    if keyboard.is_pressed('f8'):          
        print('F8 pressed, script ended.')
        break

    s = random_8()
    keyboard.write(s)                      
    keyboard.send('enter')                 
    time.sleep(0.1)
#by afatcat-xie
