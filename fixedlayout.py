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
        # # yes, we are dynamically adding properties universally to the base Widget class
        # # this is generally unwise behavior, but I'm not able to modify Widget directly
        # Widget.pos_hint_x = NumericProperty(0.0)
        # Widget.pos_hint_y = NumericProperty(0.0)
        # Widget.pos_hint = ReferenceListProperty(Widget.pos_hint_x, Widget.pos_hint_y)
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

    def pos_hint_to_pos(self, pos_hint):
        #return pos_hint
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
            c.size = self.size_hint_to_size(c.true_screen_size)
            c.pos = self.pos_hint_to_pos((0,0))
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

    def pos_hint_to_pos(self, pos_hint):
        #return pos_hint
        pos = [
            self.true_scaler(pos_hint[X]) + self.x_offset,
            self.true_scaler(pos_hint[Y]) + self.y_offset
        ]
        return pos

    def size_hint_to_size(self, size_hint):
        #return size_hint
        size = [
            self.true_scaler(size_hint[X]),
            self.true_scaler(size_hint[Y])
        ]
        return size

    def do_layout(self, *args, **kwargs):
        self.calc_scale_to_window()
        for c in self.children:
            if 'size_hint' in dir(c):
                c.size = self.size_hint_to_size(c.size_hint)
            if 'pos_hint' in dir(c):
                c.pos = self.pos_hint_to_pos(c.pos_hint)
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

class FixedImageButton(ButtonBehavior, Image):
    pass
