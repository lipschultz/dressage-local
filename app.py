import sqlite3
from pathlib import Path

import pyglet

import select_image

PRODUCTION = True
FONT_COLOR_WHITE = (255, 255, 255, 127)
FONT_COLOR_BLACK = (0, 0, 0, 127)
FONT_COLOR_SUCCESS = (243, 229, 171, 168)
FONT_COLOR_FAILURE = (139, 0, 0, 168)
FONT_SIZE = 24
TIMER_DURATION = 7 * 60

DATABASE_URL = 'dressage.sqlite'
SOURCE_DIRECTORY = Path('images')

window = pyglet.window.Window(fullscreen=PRODUCTION, caption='Dressage')
db = sqlite3.connect(DATABASE_URL,
                     detect_types=sqlite3.PARSE_DECLTYPES
                     )
db.row_factory = sqlite3.Row


def get_x_width(obj):
    obj_x = obj.x
    width = getattr(obj, 'content_width', obj.width)
    if obj.anchor_x == 'right':
        obj_x = obj_x - width
    elif obj.anchor_x == 'center':
        obj_x = obj_x - width // 2

    return obj_x, width


def get_y_height(obj):
    obj_y = obj.y
    height = getattr(obj, 'content_height', obj.height)
    if obj.anchor_y == 'top':
        obj_y = obj_y - height
    elif obj.anchor_y == 'center':
        obj_y = obj_y - height // 2

    return obj_y, height


def get_bounding_box(obj):
    x, width = get_x_width(obj)
    y, height = get_y_height(obj)
    return x, y, width, height


def is_within(x, y, obj):
    obj_x, obj_y, obj_width, obj_height = get_bounding_box(obj)

    if False:
        print(obj_x, '<=', x, '<=', obj_x + obj_width, '=', obj_x, '+', obj_width, '\t', obj.anchor_x)
        print('\t', (obj_x <= x <= obj_x + obj_width))
        print(obj_y, '<=', y, '<=', obj_y + obj_height, '=', obj_y, '+', obj_height, '\t', obj.anchor_y)
        print('\t', (obj_y <= y <= obj_y + obj_height))

    return (obj_x <= x <= obj_x + obj_width) and (obj_y <= y <= obj_y + obj_height)


class BackgroundBox:
    def __init__(self, foreground_object, border_width=5):
        self.object = foreground_object
        self.border_width = border_width
        self.color = FONT_COLOR_BLACK

    @property
    def x(self):
        return get_x_width(self.object)[0] - self.border_width

    @property
    def anchor_x(self):
        return 'left'

    @property
    def y(self):
        return get_y_height(self.object)[0] - self.border_width

    @property
    def anchor_y(self):
        return 'bottom'

    @property
    def width(self):
        return get_x_width(self.object)[1] + 2*self.border_width

    @property
    def height(self):
        return get_y_height(self.object)[1] + 2*self.border_width

    def draw(self):
        box = pyglet.shapes.Rectangle(x=self.x, y=self.y, width=self.width, height=self.height, color=self.color[:3])
        box.opacity = self.color[3]

        box.draw()
        self.object.draw()


class Image:
    def __init__(self, filename, window):
        self.filepath = Path(filename)
        self.image = pyglet.image.load(self.filename)
        self.sprite = pyglet.sprite.Sprite(img=self.image)
        self.scale(window.width, window.height)

    @property
    def filename(self):
        return str(self.filepath)

    def scale(self, window_width, window_height):
        width_factor = window_width / self.image.width
        height_factor = window_height / self.image.height

        factor = min(width_factor, height_factor)

        new_width = self.image.width * factor
        new_height = self.image.height * factor
        self.sprite.update(scale=factor,
                           x=(window_width - new_width) // 2,
                           y=(window_height - new_height) // 2,
                           )

    def draw(self, window):
        self.scale(window.width, window.height)
        self.sprite.draw()


class Rating:
    def __init__(self, rating):
        self.rating = rating
        self.stars = [
            BackgroundBox(pyglet.text.Label(
                str(i+1),
                font_name='Times New Roman',
                font_size=FONT_SIZE,
                color=FONT_COLOR_WHITE,
                x=5, y=5,
                anchor_x='left',
                anchor_y='top',
            ))
            for i in range(5)
        ]

    @property
    def x(self):
        return min(get_x_width(s)[0] for s in self.stars)

    @property
    def width(self):
        x_plus_widths = [sum(get_x_width(s)) for s in self.stars]
        return max(x_plus_widths) - self.x

    @property
    def anchor_x(self):
        return 'left'

    @property
    def y(self):
        return min(get_y_height(s)[0] for s in self.stars)

    @property
    def height(self):
        y_plus_heights = [sum(get_y_height(s)) for s in self.stars]
        return max(y_plus_heights) - self.y

    @property
    def anchor_y(self):
        return 'bottom'

    def update(self, window):
        x_offset = 5
        for i, star_box in enumerate(self.stars):
            star_box.object.x = x_offset
            x_offset += star_box.width
            star_box.object.y = window.height - 5
            if i + 1 <= self.rating:
                star_box.object.color = FONT_COLOR_BLACK
                star_box.color = FONT_COLOR_SUCCESS
            else:
                star_box.object.color = FONT_COLOR_WHITE
                star_box.color = FONT_COLOR_BLACK

    def draw(self):
        for star in self.stars:
            star.draw()

    def on_click(self, x, y, button, modifiers):
        for star in self.stars:
            if is_within(x, y, star):
                file_reference = horse_sprite.filepath.relative_to(SOURCE_DIRECTORY)
                rating = int(star.object.text)
                print(f'Recording {rating} stars for {file_reference}')
                select_image.record_rating(db, str(file_reference), rating)
                self.rating = rating
                break


class Timer:
    def __init__(self, seconds, update_frequency=1, at_zero=lambda: None):
        self.limit_seconds = seconds
        self.update_frequency = update_frequency
        self.reset()
        self.running = False
        self.at_zero = at_zero

    def reset(self):
        self.timer = self.limit_seconds

    def start(self):
        self.running = True
        pyglet.clock.schedule_interval(self.tick, 1 / self.update_frequency)
        self.tick(0)

    def pause(self):
        self.running = False
        pyglet.clock.unschedule(self.tick)

    def toggle(self):
        if self.running:
            self.pause()
        else:
            self.start()

    def tick(self, dt):
        self.timer -= dt

        if self.timer <= 0:
            self.reset()
            self.at_zero()

    def __str__(self):
        return f'{int(self.timer // 60):01}:{int(self.timer % 60):02}'


window_button = BackgroundBox(pyglet.text.Label(
    'W',
    font_name='Times New Roman',
    font_size=FONT_SIZE,
    color=FONT_COLOR_WHITE,
    x=5, y=5,
    anchor_x='right',
    anchor_y='top',
))


def update_window_button():
    window_button.object.x = get_x_width(refresh_button)[0] - 10
    window_button.object.y = timer_button.y - 10


refresh_button = BackgroundBox(pyglet.text.Label(
    'R',
    font_name='Times New Roman',
    font_size=FONT_SIZE,
    color=FONT_COLOR_WHITE,
    x=5, y=5,
    anchor_x='right',
    anchor_y='top',
))


def pre_refresh_button_draw():
    refresh_button.object.x = window.width - 5
    refresh_button.object.y = timer_button.y - 10


def get_new_image():
    global horse_sprite
    global horse_rating
    image = None
    n_failures = 0
    while image is None:
        only_unrated = n_failures < 5
        image, rating = select_image.select_random_horse(db, SOURCE_DIRECTORY, only_unrated=only_unrated)
        try:
            print(SOURCE_DIRECTORY / image)
            horse_sprite = Image(SOURCE_DIRECTORY / image, window)
            horse_rating = Rating(rating)
        except (pyglet.image.codecs.ImageDecodeException, pyglet.gl.lib.GLException) as ex:
            print(f'Failed to load {image}: {ex}')
            image = None
            n_failures += 1


timer = Timer(TIMER_DURATION, at_zero=get_new_image)
timer.start()
timer_button = BackgroundBox(pyglet.text.Label(
    '0:00',
    font_name='Times New Roman',
    font_size=FONT_SIZE,
    color=FONT_COLOR_WHITE,
    x=5, y=5,
    anchor_x='right',
    anchor_y='top',
))


def pre_timer_button_draw():
    timer_button.object.x = window.width - 5
    timer_button.object.y = window.height
    timer_button.object.text = str(timer)


@window.event
def on_draw():
    window.clear()
    horse_sprite.draw(window)

    pre_timer_button_draw()
    timer_button.draw()

    update_window_button()
    window_button.draw()

    pre_refresh_button_draw()
    refresh_button.draw()

    horse_rating.update(window)
    horse_rating.draw()


@window.event
def on_mouse_press(x, y, button, modifiers):
    if is_within(x, y, window_button):
        window.set_fullscreen(not window.fullscreen)
    if is_within(x, y, timer_button):
        timer.toggle()
    if is_within(x, y, refresh_button):
        get_new_image()
        timer.reset()
    if is_within(x, y, horse_rating):
        horse_rating.on_click(x, y, button, modifiers)


get_new_image()
pyglet.app.run()
