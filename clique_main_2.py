"""
Version 2:
 - Added DIRECTIONS constant
 - Reduced player speed slightly
 - 'Escape' now quits game
 - Removed some randomness
 - Moved player movement out of Shape class (since it only uses global variables)
 - Tweaked shape placement (on creation)
 - Overhauled shapes' decision algorithm (in Shape.move)
  - Made line-of-sight infinite
  - Abandoned 'inertia' metaphor; shapes no longer keep track of their direction
  - Each shape now makes its decision based solely on the closest other shape,
  rather than accounting for *every* shape (speeding up the inner loop, and
  fixing the bug where all the shapes just migrated to the top left)
  - Shapes now always move along axis of greatest length, regardless if
  approaching or avoiding
"""

from __future__ import division, print_function
import pygame, pygame.locals, math, random

RAND = random.Random()
RAND.seed()

UP = 0
DOWN = 1
RIGHT = 2
LEFT = 3
STAY = 4
DIRECTIONS = ['up', 'down', 'right', 'left', 'stay']

PLAYER_MOVEMENT = 2
OFFSET = [0, 0]

SHAPE_TYPES = ['triangle', 'square', 'pentagon', 'hexagon', 'circle']
SHAPE_SIDES = {
    'circle': 1, 'hexagon': 6, 'pentagon': 5, 'square': 4, 'triangle': 3}
SHAPE_MEAN = {
    'circle': 35, 'hexagon': 40, 'pentagon': 45, 'square': 70, 'triangle': 80}
SHAPE_DEV = {
    'circle': 5, 'hexagon': 6, 'pentagon': 7, 'square': 9, 'triangle': 10}

MAGIC_CONSTANT = 2 / len(SHAPE_TYPES)
# if the dividend is 1, all shape types will be generated equally
# if the dividend is > 1, the distribution of shapes will be skewed in favor
#     of fewer sides.
# if the dividend is >= the divisor, only triangles will be generated.

STROKE_WIDTH = 1
NUM_SHAPES = 50
MAX_AGE = 10000

BLACK = pygame.color.Color(0,0,0)
WHITE = pygame.color.Color(255,255,255)

def main(player, shapes, size, period):

    pygame.init()
    pygame.key.set_repeat(24, 24)
    screen = pygame.display.set_mode(size)
    TICK = pygame.locals.USEREVENT + 1
    pygame.time.set_timer(TICK, period)
    running = True

    while running:
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False
                pygame.quit()

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_UP:
                    move_player(UP)

                elif event.key == pygame.K_DOWN:
                    move_player(DOWN)

                elif event.key == pygame.K_RIGHT:
                    move_player(RIGHT)

                elif event.key == pygame.K_LEFT:
                    move_player(LEFT)

                elif event.key == pygame.K_ESCAPE:
                    running = False
                    pygame.quit()

            elif event.type == TICK:

                screen.fill(WHITE)

                # these loops must run consecutively because shapes calculate
                # new positions based on the old positions of other shapes;
                # discrete timesteps are maintained with the Shape.pos and
                # Shape.nextpos variables. A shape's actual position is only
                # updated in its draw method.
                for shape in shapes:
                    if shape != player: shape.move()
                for shape in shapes:
                    if shape != player: shape.draw(screen)
                # the player should always be on top, so it gets rendered last
                player.draw(screen)

                pygame.display.flip()

# end main()

def move_player(direction):
    # modify offset in *opposite* direction
    # (to keep "camera" centered on player)

    if direction == UP:
        OFFSET[1] += PLAYER_MOVEMENT
    elif direction == DOWN:
        OFFSET[1] -= PLAYER_MOVEMENT
    elif direction == RIGHT:
        OFFSET[0] -= PLAYER_MOVEMENT
    elif direction == LEFT:
        OFFSET[0] += PLAYER_MOVEMENT

class Shape(object):
    def __init__(self, position, shape_type, side_length, color, persona, age):
        self.pos = position
        self.nextpos = list(position)
        self.focus = None
        self.focusdist = None
        self.shape_type = shape_type
        self.side_length = side_length # for circles, side_length = radius
        self.color = color
        self.persona = persona
        self.age = age
        self.points = makepoints(self.pos, self.shape_type, self.side_length)

    def move(self):
        xpos = self.pos[0]
        ypos = self.pos[1]

        # find the nearest shape and focus attention on it
        nearest = None
        location = None
        for shape in shapes:
            if shape == player:
                xdist = xpos - (shape.pos[0] - OFFSET[0])
                ydist = ypos - (shape.pos[1] - OFFSET[1])
            else:
                xdist = xpos - shape.pos[0]
                ydist = ypos - shape.pos[1]

            totaldist = abs(xdist) + abs(ydist)

            if ((nearest == None or totaldist < location[2])
                and shape != self
                ):
                nearest = shape
                location = (xdist, ydist, totaldist)
        self.focus = nearest
        self.focusdist = location

        direction = self.where_to(nearest, location)

        if   direction == UP:    self.nextpos[1] -= 1
        elif direction == DOWN:  self.nextpos[1] += 1
        elif direction == RIGHT: self.nextpos[0] += 1
        elif direction == LEFT:  self.nextpos[0] -= 1
        # if direction == STAY:  do nothing

    def where_to(self, nearest, location):
        vote = STAY

        xdist     = location[0]
        ydist     = location[1]
        totaldist = location[2]

        approach = closer(xdist, ydist)
        avoid = further(xdist, ydist)
        assert approach != avoid

        if totaldist < self.persona.personal_space:
            vote = avoid
        else:
            if self.shape_type == nearest.shape_type:
                vote = approach
            elif abs(SHAPE_TYPES.index(self.shape_type) -
                     SHAPE_TYPES.index(nearest.shape_type)) > 2:
                vote = avoid

            rgb_tolerance = self.persona.rgb_tolerance

            red_tolerant   = ( abs(self.color.r - nearest.color.r)
                               <= rgb_tolerance)

            green_tolerant = ( abs(self.color.g - nearest.color.g)
                               <= rgb_tolerance)

            blue_tolerant  = ( abs(self.color.b - nearest.color.b)
                               <= rgb_tolerance)

            if red_tolerant and green_tolerant and blue_tolerant:
                vote = approach
            elif not red_tolerant and not green_tolerant and not blue_tolerant:
                vote = avoid

        return vote

    # end where_to()

    def draw(self, surface):

        #self.draw_line_to_focus(surface) # for debugging

        if self == player:
            pygame.draw.circle(surface, self.color, self.pos, self.side_length)
            pygame.draw.circle(surface, BLACK, self.pos,
                               self.side_length, STROKE_WIDTH)
        else:
            xpos = self.pos[0] + OFFSET[0]
            ypos = self.pos[1] + OFFSET[1]

            # if the shape isn't visible, don't bother drawing it
            offscreen = (xpos > size[0] + self.side_length or
                         xpos <          -self.side_length or
                         ypos > size[1] + self.side_length or
                         ypos <          -self.side_length)

            if not offscreen:

                if self.shape_type == 'circle':
                    pygame.draw.circle(surface, self.color, (xpos, ypos),
                                       self.side_length)
                    pygame.draw.circle(surface, BLACK, (xpos, ypos),
                                       self.side_length, STROKE_WIDTH)

                else: # praw a polygon centered at self.pos
                    pygame.draw.polygon(surface, self.color, self.offset_points())
                    pygame.draw.polygon(surface, BLACK, self.offset_points(),
                                        STROKE_WIDTH)

            #else: print("This shape (of type ", self.shape_type, ") is offscreen")

            self.update_position()
            self.age += 1
            if self.age > MAX_AGE:
                shapes.remove(self)
                shapes.append(generate_shape())

    def draw_line_to_focus(self, surface):
        focus = self.focus

        if focus != None:
            if self == player:
                x1 = self.pos[0]
                y1 = self.pos[1]
            else:
                x1 = self.pos[0] + OFFSET[0]
                y1 = self.pos[1] + OFFSET[1]

            if focus == player:
                x2 = focus.pos[0]
                y2 = focus.pos[1]
            else:
                x2 = focus.pos[0] + OFFSET[0]
                y2 = focus.pos[1] + OFFSET[1]

            x3 = x1
            y3 = y1 - 10

            pygame.draw.line(surface, BLACK, (x1, y1), (x2, y2))
            pygame.draw.line(surface, BLACK, (x2, y2), (x3, y3))

    def update_position(self):
        if self.shape_type != 'circle':
            xdiff = self.nextpos[0] - self.pos[0]
            ydiff = self.nextpos[1] - self.pos[1]
            for point in self.points:
                point[0] += xdiff
                point[1] += ydiff
        self.pos = (self.nextpos[0], self.nextpos[1])

    def offset_points(self):
        return [ [point[0] + OFFSET[0], point[1] + OFFSET[1]]
                 for point in self.points ]

# end class Shape


"""
xdist = xpos - shape.pos[0]
ydist = ypos - shape.pos[1]

If xdist is positive, they are to the left of me.
If xdist is negative, they are to the right of me.
If ydist is positive, they are above me.
If ydist is negative, they are below me.
I will reduce the axis of greatest distance if I want to get closer.
I will increase the axis of greatest distance if I want to get further.
OR
#I will randomly choose an axis to travel along.
"""
def closer(xdist, ydist):
    if xdist == ydist == 0:
        return STAY
    #if RAND.random() < 0.5:
    if abs(xdist) > abs(ydist):
        # move along the x axis
        if xdist > 0:
            return LEFT
        else:
            return RIGHT
    else:
        # move along the y axis
        if ydist > 0:
            return UP
        else:
            return DOWN

def further(xdist, ydist):
    #if RAND.random() < 0.5:
    if abs(xdist) > abs(ydist):
        # move along the x axis
        if xdist > 0:
            return RIGHT
        else:
            return LEFT
    else:
        # move along the y axis
        if ydist > 0:
            return DOWN
        else:
            return UP


class Personality(object):
    def __init__(self, shape_type):
        self.rgb_tolerance = 150
        #self.size_tolerance = int(RAND.gauss(SHAPE_MEAN[shape_type] / 2,
                                             #SHAPE_DEV[shape_type] / 2))
        self.personal_space = SHAPE_MEAN[shape_type]

# end class Personality

def makepoints(position, shape_type, side_length):
    halfside = side_length / 2

    if shape_type == 'circle':
        return None

    elif shape_type == 'triangle':
        h = math.sqrt(side_length**2 - (side_length/2)**2)
        apothem = h / 2
        top = [position[0], position[1] - apothem]
        botleft = [position[0] - halfside, position[1] + apothem]
        botright = [position[0] + halfside, position[1] + apothem]
        return (top, botleft, botright)

    elif shape_type == 'square':
        topleft = [position[0] - halfside, position[1] - halfside]
        topright = [topleft[0] + side_length, topleft[1]]
        botleft = [topleft[0], topleft[1] + side_length]
        botright = [topright[0], topright[1] + side_length]
        return (topleft, topright, botright, botleft)

    else:
        numsides = SHAPE_SIDES[shape_type]
        apothem = side_length / (2 * math.tan(math.pi / numsides))

        angle = ((numsides - 2) * math.pi) / (numsides * 2)
        xoffset = side_length * math.sin(angle)
        yoffset = side_length * math.cos(angle)
        radius = math.sqrt(halfside**2 + apothem**2)

        if shape_type == 'pentagon':
            top = [position[0], position[1] - radius]
            second = [position[0] + xoffset, top[1] + yoffset]
            third = [position[0] + halfside, position[1] + apothem]
            fourth = [position[0] - halfside, position[1] + apothem]
            fifth = [position[0] - xoffset, top[1] + yoffset]
            return (top, second, third, fourth, fifth)

        elif shape_type == 'hexagon':
            topleft = [position[0] - halfside, position[1] - apothem]
            topright = [position[0] + halfside, position[1] - apothem]
            right = [position[0] + radius, position[1]]
            botright = [position[0] + halfside, position[1] + apothem]
            botleft = [position[0] - halfside, position[1] + apothem]
            left = [position[0] - radius, position[1]]
            return (topleft, topright, right, botright, botleft, left)

        else:
            print('unkown shape, type:', shape_type)
            assert False

# end makepoints()

def choose_shape():
    for shape_type in SHAPE_TYPES:
        if shape_type == 'circle':
            return shape_type
        elif RAND.random() < MAGIC_CONSTANT:
            return shape_type

def generate_shape(random_age=False):
    if random_age:
        age = RAND.randint(0, MAX_AGE-1)
    else:
        age = 0

    r = g = b = 255
    while r == 255 and g == 255 and b == 255: # only the player may be white
        r = RAND.randint(0,255)
        g = RAND.randint(0,255)
        b = RAND.randint(0,255)
    x = RAND.randint(-50,size[0]+50) - OFFSET[0]
    y = RAND.randint(-50,size[1]+50) - OFFSET[1]
    # new shapes always appear onscreen - problem?

    shape_type = choose_shape()
    shape_size = 0
    while shape_size <= 0:
        shape_size = RAND.gauss(SHAPE_MEAN[shape_type], SHAPE_DEV[shape_type])

    shape = Shape( (x,y),
                   shape_type,
                   int(shape_size),
                   pygame.color.Color(r, g, b),
                   Personality(shape_type),
                   age )
    return shape

def generate_shapes():
    shapes = []
    for i in range(NUM_SHAPES):
        shape = generate_shape(True)
        shapes.append(shape)
    return shapes



size = (1200, 900)
period = 25

player = Shape( (int(size[0]/2), int(size[1]/2)),
                'circle',
                25,
                WHITE,
                None,
                None )

shapes = generate_shapes()
shapes.append(player)

main(player, shapes, size, period)
