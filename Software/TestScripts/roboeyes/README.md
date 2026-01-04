For now, use `roboeyes_desktop.py`

The [roboeyes library](https://github.com/FluxGarage/RoboEyes) animates robotic eyes on a SSD1306 OLED screen. [Similar micropython version](https://github.com/mchobby/micropython-roboeyes).

This is a port to normal desktop-based python code so that I can animate eyes on Orion's Front Monitor using opencv

- The roboeyes.py file in the library uses other libraries as well, and uses the 'FrameBuf' type which has some helper drawing functions. 
    - See self.gfx.fill_rrect and self.gfx.fill_triangle, which uses this https://github.com/mchobby/esp8266-upy/blob/master/FBGFX/lib/fbutil.py#L154 etc.
    - https://github.com/peter-l5/framebuf2 

## TODO: finish porting and combine scripts

The original Roboeyes library has the following functionality:
- [Youtube: #1 - Smoothly Animated Robot Eyes on OLED Displays with the Robo Eyes Library](https://www.youtube.com/watch?v=ibSaDEkfUOI)
    - Laugh -> strong vertical shaking - pairs with Happy or Angry mood
    - Confused -> strong horizontal shaking, like it hit obstacle
    - Curiousity mode -> Corresponding eye grows when looking to respecitive side i.e. "Hey where is everyone? What's going on"
    - Flicker -> flickering horizontal / vertical by 1 pixels. Pairing horizontal with 'scared' or "angry" mood emphasizes the mood.
- [Youtube:  #2 - Getting Started With the Free Robo Eyes Arduino Library ](https://www.youtube.com/watch?v=WtLWc5zzrmI)
    - 