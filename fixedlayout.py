from kivy.uix.scatterlayout import ScatterLayout
from kivy.properties import ObjectProperty
from kivy.core.window import Window

class FixedLayout(ScatterLayout):
    
    screensize = ObjectProperty((1920, 1080))

    def __init__(self, **kw):
        kw['size'] = (Window.width, Window.height)
        kw['size_hint'] = (None, None)
        kw['do_scale'] = False
        kw['do_translation'] = False
        kw['do_rotation'] = False
        super(FixedLayout, self).__init__(**kw)
        self.init_diff = [
            self.screensize[0]-Window.width,
            self.screensize[1]-Window.height
        ]
        self.__fit_to_window()
        Window.bind(system_size=self.__fit_to_window)

    def __fit_to_window(self, *args):
        window_ratio = Window.width/float(Window.height)
        if window_ratio>1:
            self.__fit_to_landscape_window()
        else:
            self.__fit_to_portrait_window()


    def __fit_to_landscape_window(self, *args):
        self.rotation = 0
        screen_ratio = self.screensize[0]/float(self.screensize[1])
        window_ratio = Window.width/float(Window.height)
        if screen_ratio > window_ratio:
            self.scale = Window.width/float(self.screensize[0])
        else:
            self.scale = Window.height/float(self.screensize[1])
        frame_left = (self.init_diff[0]/2)*self.scale
        frame_bottom = (self.init_diff[1]/2)*self.scale
        self.center = (
            Window.width/2-frame_left,
            Window.height/2-frame_bottom
        )

    def __fit_to_portrait_window(self, *args):
        self.rotation = -90
        screen_ratio = self.screensize[1]/float(self.screensize[0])
        window_ratio = Window.width/float(Window.height)
        if screen_ratio > window_ratio:
            self.scale = Window.width/float(self.screensize[1])
        else:
            self.scale = Window.height/float(self.screensize[0])
        frame_left = (self.init_diff[1]/2)*self.scale
        frame_bottom = (self.init_diff[0]/2)*self.scale
        self.center = (
            Window.width/2-frame_left,
            Window.height/2+frame_bottom
        )
