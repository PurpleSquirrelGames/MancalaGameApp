from kivy.uix.layout import Layout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import OptionProperty, VariableListProperty
from kivy.core.window import Window
from kivy.uix.behaviors.button import ButtonBehavior
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy.config import Config

X = 0
Y = 1
WIDTH = 0
HEIGHT = 1

class FixedLayoutRoot(Layout):

    true_screen_size = VariableListProperty([1920, 1080], limit=2)

    def __init__(self, **kwargs):
        super(FixedLayoutRoot, self).__init__(**kwargs)
        fbind = self.fbind
        update = self._trigger_layout
        #fbind('children', update)
        # fbind('parent', update)
        fbind('size', update)
        fbind('pos', update)
        self.calc_scale_to_window()


    def calc_scale_to_window(self, *args, **kwargs):
        #print "FLR size", self.size
        self.window_width, self.window_height = self.size
        screen_ratio = self.true_screen_size[WIDTH]/float(self.true_screen_size[HEIGHT])
        window_ratio = self.window_width/float(self.window_height)
        if screen_ratio > window_ratio:
            self.ratio = self.window_width/float(self.true_screen_size[WIDTH])
            pixel_height = self.ratio*self.true_screen_size[HEIGHT]
            self.x_offset = 0
            self.y_offset = int((self.window_height - pixel_height) / 2)
        else:
            self.ratio = self.window_height/float(self.true_screen_size[HEIGHT])
            pixel_width = self.ratio*self.true_screen_size[WIDTH]
            self.x_offset = int((self.window_width - pixel_width) / 2)
            self.y_offset = 0
        # print "RATIO", self.ratio
        # print "OFFSETS", self.x_offset, self.y_offset

    def true_place_to_pos(self, true_place):
        #return true_place
        pos = [
            int(self.ratio * float(true_place[X])) + self.x_offset,
            int(self.ratio * float(true_place[Y])) + self.y_offset
        ]
        return pos

    def true_size_to_size(self, true_size):
        #return true_size
        size = [
            int(self.ratio * float(true_size[X])),
            int(self.ratio * float(true_size[Y]))
        ]
        return size

    # def redraw_canvas(self):
    #     self.canvas.clear()
    #     with self.canvas:
    #         Color(*self.window_background_color)
    #         Rectangle(pos=self.pos, size=self.size)
    #         print "CANVAS", self.pos, self.size

    def do_layout(self, *args, **kwargs):
        self.calc_scale_to_window()
        # self.redraw_canvas()
        for c in self.children:
            c.size = self.true_size_to_size(c.true_screen_size)
            c.pos = self.true_place_to_pos((0,0))
            c.x_offset = self.x_offset
            c.y_offset = self.y_offset

    # def add_widget(self, widget, index=0):
    #     widget.bind(
    #         size=self._trigger_layout,
    #         pos=self._trigger_layout
    #     )
    #     return super(FixedLayoutRoot, self).add_widget(widget, index)

    # def remove_widget(self, widget):
    #     widget.unbind(
    #         size=self._trigger_layout,
    #         pos=self._trigger_layout
    #     )
    #     return super(FixedLayoutRoot, self).remove_widget(widget)












class FixedLayout(Layout):

    true_screen_size = VariableListProperty([1920, 1080], limit=2)


    # Config.set('graphics', 'width', 1920)
    # Config.set('graphics', 'height', 1080)
    # Config.set('graphics', 'fullscreen', 'fake')
    # Config.set('graphics', 'fullscreen', 'auto')
    # Window.fullscreen = True

    def __init__(self, **kwargs):
        self.x_offset, self.y_offset = (0,0)
        super(FixedLayout, self).__init__(**kwargs)
        fbind = self.fbind
        update = self._trigger_layout
        # fbind('children', update)
        # fbind('parent', update)
        fbind('size', update)
        fbind('pos', update)
        self.calc_scale_to_window()


#get_window_matrix(x=0, y=0)
# to_window(x, y, initial=True, relative=False)
# Transform local coordinates to window coordinates. See relativelayout for details on the coordinate systems.


    def calc_scale_to_window(self, *args, **kwargs):
        #print "FL size", self.size
        self.window_width, self.window_height = self.size
        screen_ratio = self.true_screen_size[WIDTH]/float(self.true_screen_size[HEIGHT])
        window_ratio = self.window_width/float(self.window_height)
        if screen_ratio > window_ratio:
            self.ratio = self.window_width/float(self.true_screen_size[WIDTH])
            pixel_height = self.ratio*self.true_screen_size[HEIGHT]
        else:
            self.ratio = self.window_height/float(self.true_screen_size[HEIGHT])
            pixel_width = self.ratio*self.true_screen_size[WIDTH]
        # print "RATIO", self.ratio
        # print "OFFSETS", self.x_offset, self.y_offset


    def true_scaler(self, something):
        return int(self.ratio * float(something))

    def true_place_to_pos(self, true_place):
        #return true_place
        pos = [
            self.true_scaler(true_place[X]) + self.x_offset,
            self.true_scaler(true_place[Y]) + self.y_offset
        ]
        return pos

    def true_size_to_size(self, true_size):
        #return true_size
        size = [
            self.true_scaler(true_size[X]),
            self.true_scaler(true_size[Y])
        ]
        return size

    def do_layout(self, *args, **kwargs):
        self.calc_scale_to_window()
        for c in self.children:
            if 'true_size' in dir(c):
                c.size = self.true_size_to_size(c.true_size)
            if 'true_place' in dir(c):
                c.pos = self.true_place_to_pos(c.true_place)
            if 'true_font_size' in dir(c):
                c.font_size = self.true_scaler(c.true_font_size)
            # if "Label" in str(c.__class__):
            #     print "LABEL", c.text
            #     print "       pos  ", c.pos 
            #     print "       size ", c.size 
            #     print "       font ", c.font_size

    def add_widget(self, widget, index=0):
        widget.size = (1920, 1080)
        widget.bind(
            size=self._trigger_layout,
            pos=self._trigger_layout
        )
        return super(FixedLayout, self).add_widget(widget, index)

    def remove_widget(self, widget):
        widget.unbind(
            size=self._trigger_layout,
            pos=self._trigger_layout
        )
        return super(FixedLayout, self).remove_widget(widget)

class FixedImageButton(ButtonBehavior, Image):
    pass
