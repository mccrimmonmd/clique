"""
Version 1:
 - It begins
 - For some reason, this version of the decision code (in Shape.move) just makes
 every shape move up and to the left
"""

from __future__ import division
import pygame, pygame.locals, math, random

RAND = random.Random()
RAND.seed()

UP = 0
DOWN = 1
RIGHT = 2
LEFT = 3
STAY = 4

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

LINE_OF_SIGHT = 500
STROKE_WIDTH = 1
NUM_SHAPES = 50
MAX_AGE = 10000

BLACK = pygame.color.Color(0,0,0)
WHITE = pygame.color.Color(255,255,255)

def main(player, shapes, size, period):

    pygame.init()
    pygame.key.set_repeat(25, 25)
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
                    player.move_player(UP)

                elif event.key == pygame.K_DOWN:
                    player.move_player(DOWN)

                elif event.key == pygame.K_RIGHT:
                    player.move_player(RIGHT)

                elif event.key == pygame.K_LEFT:
                    player.move_player(LEFT)

                #elif event.key == pygame.K_SPACE:
                    #pass

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

class Shape(object):

    def __init__(self, position, shape_type, side_length, color, persona, age=0):
        self.pos = position
        self.nextpos = list(position)
        self.direction = STAY
        self.shape_type = shape_type
        self.side_length = side_length # for circles, side_length = radius
        self.color = color
        self.persona = persona
        self.age = age
        self.points = makepoints(self.pos, self.shape_type, self.side_length)

    def move(self):

        # KEEP TRACK OF CURRENT DIRECTION; VOTE TO CHANGE IT OR NOT
        # (shapes should have a certain amount of inertia)

        # the shape should lose its inertia if its personal space is invaded #
        if RAND.random() < .25: # shape is changing direction

            # 0 for UP, 1 for DOWN, 2 for RIGHT, 3 for LEFT, 4 for STAY
            votes = [0,0,0,0,0]

            self_type = self.shape_type
            self_r = self.color.r
            self_g = self.color.g
            self_b = self.color.b
            self_size = self.side_length
            rgb_tolerance = self.persona.rgb_tolerance
            #size_tolerance = self.persona.size_tolerance
            space_tolerance = self.persona.personal_space

            xpos = self.pos[0]
            ypos = self.pos[1]

            ups = 0
            downs = 0
            rights = 0
            lefts = 0
            stays = 0

            for shape in shapes:
                xdist = xpos - shape.pos[0]
                ydist = ypos - shape.pos[1]
                totaldist = math.sqrt(xdist**2 + ydist**2)
                if totaldist < LINE_OF_SIGHT:
                    approach = closer(xdist, ydist)
                    avoid = further(xdist, ydist)

                    if approach == 0 or avoid == 0: ups += 1
                    if approach == 1 or avoid == 1: downs += 1
                    if approach == 2 or avoid == 2: rights += 1
                    if approach == 3 or avoid == 3: lefts += 1
                    if approach == 4 or avoid == 4: stays += 1
                    assert approach != avoid
                    #print approach, avoid

                    if totaldist < space_tolerance:
                        votes[avoid] += space_tolerance - int(totaldist)

                    if self_type != shape.shape_type:
                        #votes[approach] += 3
                        #votes[STAY] += 1
                    #else:
                        votes[avoid] += 3

                    if (self_r - rgb_tolerance <=
                        shape.color.r <=
                        self_r + rgb_tolerance):

                        votes[approach] += 1
                    #else:
                        #votes[avoid] += 1

                    if (self_g - rgb_tolerance <=
                        shape.color.g <=
                        self_g + rgb_tolerance):

                        votes[approach] += 1
                    #else:
                        #votes[avoid] += 1

                    if (self_b - rgb_tolerance <=
                        shape.color.b <=
                        self_b + rgb_tolerance):

                        votes[approach] += 1
                    #else:
                        #votes[avoid] += 1

                    #if (self_size - size_tolerance <=
                        #shape.side_length <=
                        #self_size + size_tolerance):

                        #votes[approach] += 1
                    #else:
                        #votes[avoid] += 1

            direction = bestvote(votes)

            print votes, ups, downs, rights, lefts, stays

        else: # shape is not changing direction
            direction = self.direction

        if   direction == UP:    self.nextpos[1] -= 1
        elif direction == DOWN:  self.nextpos[1] += 1
        elif direction == RIGHT: self.nextpos[0] += 1
        elif direction == LEFT:  self.nextpos[0] -= 1
        # if direction == STAY:  do nothing

        self.direction = direction

    def move_player(self, direction):
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

    def draw(self, surface):
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

    def update_position(self):
        if self.shape_type != 'circle':
            xdiff = self.nextpos[0] - self.pos[0]
            ydiff = self.nextpos[1] - self.pos[1]
            for point in self.points:
                point[0] += xdiff
                point[1] += ydiff
        self.pos = (self.nextpos[0], self.nextpos[1])

    def offset_points(self):
        return [[point[0]+OFFSET[0], point[1]+OFFSET[1]] for point in self.points]

# end class Shape

def bestvote(votes):
    maxpos = 0
    maxval = votes[0]
    for i in range(1, len(votes)):
        if votes[i] >= maxval:
            maxpos = i
            maxval = votes[i]
    return maxpos


#xdist = xpos - shape.pos[0]
#ydist = ypos - shape.pos[1]
"""
If xdist is positive, they are to the left of me.
If xdist is negative, they are to the right of me.
If ydist is positive, they are above me.
If ydist is negative, they are below me.
I will reduce the axis of greatest distance if I want to get closer.
I will increase the axis of least distance if I want to get further.
OR
I will randomly choose an axis to travel along.
"""
def closer(xdist, ydist):
    if xdist == ydist == 0:
        return STAY
    if RAND.random() < 0.5:
    #if xdist > ydist:
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
    if RAND.random() < 0.5:
    #if xdist < ydist:
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
        self.rgb_tolerance = int(RAND.gauss(50, 10))
        #self.size_tolerance = int(RAND.gauss(SHAPE_MEAN[shape_type] / 2,
                                             #SHAPE_DEV[shape_type] / 2))
        self.personal_space = int(RAND.gauss(SHAPE_MEAN[shape_type] * 2,
                                             SHAPE_DEV[shape_type] / 2))

        print self.rgb_tolerance, self.personal_space

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
        print(shape_type)
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
    x = RAND.randint(0,size[0]) - OFFSET[0]
    y = RAND.randint(0,size[1]) - OFFSET[1]

    shape_type = choose_shape()
    shape_size = 0
    while shape_size <= 0:
        shape_size = RAND.gauss(SHAPE_MEAN[shape_type], SHAPE_DEV[shape_type])

    shape = Shape( (x,y), # new shapes always appear onscreen - problem?
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
