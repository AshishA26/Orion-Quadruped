There is a robot eye library that animates robotic eyes on a SSD1306 OLED screen using micropython.

This ports to normal desktop-based python code so that I can animate eyes on a monitor using opencv

https://github.com/mchobby/micropython-roboeyes. The roboeyes.py file in the library uses other libraries as well, and uses the 'FrameBuf' type which has some helper drawing functions. 
- See self.gfx.fill_rrect and self.gfx.fill_triangle, which uses this https://github.com/mchobby/esp8266-upy/blob/master/FBGFX/lib/fbutil.py#L154 etc.
- https://github.com/peter-l5/framebuf2 