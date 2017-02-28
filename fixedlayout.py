from kivy.uix.layout import Layout
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import OptionProperty, VariableListProperty, ObjectProperty, NumericProperty, ReferenceListProperty
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

    def pos_hint_to_pos(self, pos_hint):
        pos = [
            int(self.ratio * float(pos_hint[X])) + self.x_offset,
            int(self.ratio * float(pos_hint[Y])) + self.y_offset
        ]
        return pos

    def size_hint_to_size(self, size_hint):
        #return size_hint
        size = [
            int(self.ratio * float(size_hint[X])),
            int(self.ratio * float(size_hint[Y]))
        ]
        return size

    def do_layout(self, *args, **kwargs):
        self.calc_scale_to_window()
        # self.redraw_canvas()
        for c in self.children:
            c.size = self.size_hint_to_size(c.true_screen_size)
            c.pos = self.pos_hint_to_pos((0,0))
            c.x_offset = self.x_offset
            c.y_offset = self.y_offset


class FixedLayout(Layout):

    true_screen_size = VariableListProperty([1920, 1080], limit=2)

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

    def true_scaler(self, something):
        return int(self.ratio * float(something))

    def pos_hint_to_pos(self, pos_hint, spot):
        truex = pos_hint[X] - spot[X]
        truey = pos_hint[Y] - spot[Y]
        pos = [
            self.true_scaler(truex) + self.x_offset,
            self.true_scaler(truey) + self.y_offset
        ]
        return pos

    def size_hint_to_size(self, size_hint):
        size = [
            self.true_scaler(size_hint[X]),
            self.true_scaler(size_hint[Y])
        ]
        return size

    def do_layout(self, *args, **kwargs):
        self.calc_scale_to_window()
        for c in self.children:
            if 'true_spot' not in dir(c):
                c.true_spot = (0, 0)
            if 'size_hint' in dir(c):
                c.size = self.size_hint_to_size(c.size_hint)
            if 'pos_hint' in dir(c):
                c.pos = self.pos_hint_to_pos(c.pos_hint, c.true_spot)
            if 'true_font_size' in dir(c):
                c.font_size = self.true_scaler(c.true_font_size)

    def add_widget(self, widget, index=0):
        widget.size = (1920, 1080)
        widget.bind(
           pos_hint=self._trigger_layout
        )
        return super(FixedLayout, self).add_widget(widget, index)

    def remove_widget(self, widget):
        widget.unbind(
            pos_hint=self._trigger_layout
        )
        return super(FixedLayout, self).remove_widget(widget)

class FixedImage(Image):

    true_screen_size = VariableListProperty([1920, 1080], limit=2)
    true_spot = ObjectProperty((0,0))

class FixedImageButton(ButtonBehavior, FixedImage):
    pass
