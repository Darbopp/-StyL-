from kivy.clock import Clock as kivyClock
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Line

class NowBar(InstructionGroup):
    def __init__(self, botleft, size, padding, speed):
        super(NowBar, self).__init__()

        self.x1 = botleft[0] + padding
        self.x2 = botleft[0] + size[0] - padding
        self.y1 = botleft[1]
        self.y2 = botleft[1] + size[1]

        self.speed = speed # pixels per second
        self.playing = False

        self.x = self.x1
        self.bar = Line(points=[self.x, self.y1, self.x, self.y2], width=2)

        self.add(Color(.2, .8, .6))
        self.add(self.bar)

    def play(self):
        self.playing = True

    def stop(self):
        self.playing = False

    def toggle(self):
        self.playing = not self.playing

    def on_update(self):
        dt = kivyClock.frametime
        
        if self.playing:
            self.x = self.x + self.speed * dt
            if self.x >= self.x2:
                # hit the right bounds of the box
                self.playing = False
                self.x = self.x1
        else:
            # not playing, make sure the bar is all the way left lol
            self.x = self.x1

        self.bar.points = [self.x, self.y1, self.x, self.y2]