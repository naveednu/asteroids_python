#-*- coding: utf-8 -*- 
from Tkinter import *
import tkFont
import math
import time
import random
from math import sin, cos, radians
import numpy as np
"""
Python implementation of Asteroids game
"""

ASTEROID_SMALL = 5
ASTEROID_MEDIUM = 10
ASTEROID_LARGE = 15
SPEEDS = [10,1,5]

class Engine(object):
    """  
        Used to perform rotation, translation and object rotation.
    """
    @staticmethod
    def rotate(point, angle):
        # Given a point and angle, return the rotation matrix required to rotate the point
        rad = radians(angle)
        cos_a = cos(rad)
        sin_a = sin(rad)
        m = np.matrix([[cos_a, -sin_a], [sin_a, cos_a]])
        return point * m

    @staticmethod
    def rotate_obj(mat, angle, center):
        # Given the coordinates of an object (in matrix form) rotate it along with given center point and angle 
        # return the resulting rotated matrix
        coords = mat - center
        res = Engine.rotate(coords, angle)
        return res + center

    @staticmethod
    def move_obj(mat, angle, center, speed = 1):
        # Given the object matrix, move it with respect to center point towards the given angle
        # speed parameter is optional
        coords = mat - center
        coords[:,0] += speed * cos(angle)
        coords[:,1] += speed * sin(angle)
        return coords + center

    @staticmethod
    def detect_collision(pt1, pt2, r1, r2):
        # Given two center points and the radii of objects, detect if objects have collided
        dist = math.sqrt((pt1[0]-pt2[0])*(pt1[0]-pt2[0]) + (pt1[1]-pt2[1])*(pt1[1]-pt2[1]));
        if dist <= (r1+r2):
            return True
        return False
    
    @staticmethod
    def rotate_center(angle, coords):
        # Given object coordinates, rotate it to change its direction
        m = np.matrix(coords).reshape((len(coords)/2,2))
        final_coords = Engine.rotate_obj(m, angle, m[2]) 
        final_coords = final_coords.reshape((1,len(coords))).getA1()
        tp = tuple(final_coords)
        return tp

class Bullet(object):
    """ 
        Bullets are fired from the ship and points to ship's angle
        Each bullet is added to ship's bullet list which is later used to detect collision
    """
    def __init__(self, canv, angle, start, ship):
        # Create bullet pointed to given angle starting from start point
        self._canv = canv
        self._oval = self._canv.create_oval([start[0], start[1], start[0]+4, start[1]+4], fill='white')
        self.dist = 300
        self._angle = angle
        self._ship = ship
        self._moveit()

    def get_coords(self):
        # returns coordinate as matrix
        return np.matrix(self._canv.coords(self._oval)).reshape((2,2))

    def _moveit(self):
        # Move bullet with respect to current angle
        # if bullet goes offscreen it is removed from the canvas
        # bullet travels maximum distance defined in self.dist and discarded afterwards
        m = np.matrix(self._canv.coords(self._oval)).reshape((2,2))
        if (m[:,1] < 0).any() or (m[:,1] > self._canv.winfo_height()).any():
            # off y
            self._canv.delete(self._oval)
            self._ship.bullets.remove(self)
        elif (m[:,0] < 0).any() or (m[:,0] > self._canv.winfo_width()).any():
            # off x
            self._canv.delete(self._oval)
            self._ship.bullets.remove(self)
        else:
            fc = Engine.move_obj(m, self._angle, m[0])
            fc = fc.reshape((1,4)).getA1()
            self._canv.coords(self._oval, tuple(fc))
            if self.dist > 0.0:
                self.dist -= 1
                self._canv.after(3, self._moveit)
            else:
                # travelled max distance, remove from ship's bullet list
                self._canv.delete(self._oval)
                self._ship.bullets.remove(self)

class Asteroid(object):
    """ 
        Asteroid appears from given start point and start moving in the angle direction with given speed
        Each asteroid could be of different size
        Bullet collision detection is performed with every moment
    """
    def __init__(self, canv, angle, start, size, speed, game = None):
        self._canv = canv
        self._size = size
        x, y = start[0], start[1]
        self._coord = [(x,y),(x+size,y),(x+size,y-size/2.0),(x+size*2,y-size/2.0),(x+size*2,y),(x+size*3,y),(x+size*3,y+size+size/2.0),(x+size+size/2,y+size*2),(x,y+size+size/2)]
        self._oval = self._canv.create_polygon(self._coord, outline='white', fill='', tags=('Asteroid'))
        self._speed = speed
        self._angle = angle
        self._game = game
        self._ship = self._game.ship
        self._rotate_center(math.degrees(angle))
        self._job = self._canv.after(100, self._moveit)

    def _rotate_center(self, angle):
        # rotate the center point of asteroid
        updated_center = Engine.rotate_center(angle, self._canv.coords(self._oval))
        self._canv.coords(self._oval, updated_center)
        
    def get_coords(self):
        # returns coordinates as matrix
        return np.matrix(self._canv.coords(self._oval)).reshape((len(self._coord),2))

    def _detect_bullet_collision(self):
        # Check for collision with ship's bullets
        # If large size asteroid collides with bullet, it is broken down to smaller pieces which start moving in random directions
        # Smallest size asteroids are simply removed
        if not self._ship:
            return False
        m = self.get_coords()
        cent = (m[0:1].getA1()[0] + self._size/2, m[0:1].getA1()[1] + self._size/2)
        for bullet in self._ship.bullets:
            bmat = bullet.get_coords()
            if Engine.detect_collision(bmat[0:1].getA1(), cent, 4, self._size):
                self._canv.itemconfigure(self._oval, fill='red')
                self._canv.update_idletasks()
                self._canv.after_cancel(self._job)
                self._job = None
                self._canv.delete(self._oval)
                new_size = self._size
                if self._size == ASTEROID_LARGE: # launch medium size
                    new_size = ASTEROID_MEDIUM
                    self._game.update_score(10)
                elif self._size == ASTEROID_MEDIUM: # launch small size
                    new_size = ASTEROID_SMALL
                    self._game.update_score(20)
                elif self._size == ASTEROID_SMALL: # don't launch just return
                    self._game.update_score(30)
                    return True
                Asteroid(self._canv,  self._angle - radians(30), cent, new_size, random.choice(SPEEDS),self._game)
                Asteroid(self._canv,  self._angle + radians(30), cent, new_size, random.choice(SPEEDS),self._game)
                return True

        return False

    def _moveit(self):
        # Move asteroid with respect to current angle
        # check for ship collision with each movement
        if not self._canv.coords(self._oval):
            return
        m = np.matrix(self._canv.coords(self._oval)).reshape((len(self._coord),2))
        if (m[:,1] < 0).any() or (m[:,1] > self._canv.winfo_height()).any():
            # offscreen y, delete
            self._canv.delete(self._oval)
        elif (m[:,0] < 0).any() or (m[:,0] > self._canv.winfo_width()).any():
            # offscreen x, delete
            self._canv.delete(self._oval)
        else:
            if self._ship and self._canv.coords(self._ship._ship):
                ship_mat = self._ship.get_coords() 
                cent = (m[0:1].getA1()[0] + self._size/2, m[0:1].getA1()[1] + self._size/2)
                if Engine.detect_collision(ship_mat[0:1].getA1(), cent, 15, self._size):
                    # collided with ship, call reset_ship which can either create new ship or game over
                    self._canv.itemconfigure(self._ship._ship, fill='red')
                    self._canv.update_idletasks()
                    self._ship.reset_ship(self._game.decrease_life())

            fc = Engine.move_obj(m, self._angle, m[0])
            fc = fc.reshape((1,len(self._coord)*2)).getA1()
            self._canv.coords(self._oval, tuple(fc))
            if self._detect_bullet_collision() == False:
                self._job = self._canv.after(self._speed*5, self._moveit)

class Ship(object):
    """ 
        Ship can move Up, Down, Right and Left.
        Bullet fired move to ship's current direction
    """
    def __init__(self, canv):
        self._canv = canv
        self._scoord = [(250, 250), (235, 270),(250, 265), (265, 270)]
        self._ship = self._canv.create_polygon(self._scoord, fill='', outline='white', tags=('ship'))
        self.angle = -math.pi/2.0
        self.speed = 0.0
        self._lastfire = 0.0
        self._lastspeed = 0.0
        self._moveit()
        self.bullets = []

    def reset_ship(self, recreate):
        # Remove existing ship from canvas and if recreate is True, then create new one
        if self._ship:
            self._canv.delete(self._ship)
            self.angle = -math.pi/2.0
            self.speed = 0.0
            if recreate:
                self._ship = self._canv.create_polygon(self._scoord, outline='black', fill='gray40', tags=('ship'))

    def get_coords(self):
        # return coordinates as matrix
        return np.matrix(self._canv.coords(self._ship)).reshape((4,2))

    def _rotate_center(self, angle):
        # rotate ship's center
        updated_center = Engine.rotate_center(angle, self._canv.coords(self._ship))
        self._canv.coords(self._ship, updated_center)
        
    def _moveit(self):
        # move ship with respect to current angle
        # wrap around coordinates if ship moves out of screen
        if not self._canv.coords(self._ship):
            return
        m = np.matrix(self._canv.coords(self._ship)).reshape((4,2))
        if m[2][:,1] < 0 and m[2][:,0] > 0:
            m[:,1] += self._canv.winfo_height()
        elif m[2][:,1] > self._canv.winfo_height():
            m[:,1] -= self._canv.winfo_height()
        elif m[2][:,0] < 0:
            m[:,0] += self._canv.winfo_width()
        elif m[2][:,0] > self._canv.winfo_width():
            m[:,0] -= self._canv.winfo_width()
        fc = Engine.move_obj(m, self.angle, m[2], self.speed)
        fc = fc.reshape((1,8)).getA1()
        self._canv.coords(self._ship, tuple(fc))
        if self.speed > 0.0:
            self.speed -= 0.1
        self._canv.after(50, self._moveit)
    
    def rotate_left(self, event=None):
        # rotate 30 degrees left
        self.angle -= radians(30.0)
        self._rotate_center(30.0)
    def rotate_right(self, event=None):
        # rotate 30 degrees right
        self.angle += radians(30.0)
        self._rotate_center(-30.0)
    def speed_up(self, event=None):
        # increase speed
        if self.speed < 10.0:
            self.speed += 2.0
    def slow_down(self, event = None):
        # decrease speed
        if (time.time() - self._lastspeed) > 0.1:
            if self.speed >= 1.0:
                self.speed -= 1.0
            self._lastspeed = time.time()

    def fire(self, event):
        # Fire bullet
        if (time.time() - self._lastfire) > 0.1:
            b = Bullet(self._canv, self.angle, self._canv.coords(self._ship)[:2], self)
            self._lastfire = time.time()
            self.bullets.append(b)
            self._canv.bell()

class Game(object):
    # Main game object, bind shortcut keys and initialize everything
    def __init__(self):
        self.root = Tk()
        self.w, self.h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry("%dx%d+0+0" % (self.w,self.h))
        self.root.wm_title("Asteroids") 
        self._load_objects()
        self.root.configure(background='black')
        self.root.bind('<Left>', self.rotate_left)
        self.root.bind('<Right>', self.rotate_right)
        self.root.bind('<Up>', self.speed_up)
        self.root.bind('<Down>', self.slow_down)
        self.root.bind('<space>', self.fire)
        self.canv.bind("<Button-1>", self.resetgame)
        self.root.protocol('WM_DELETE_WINDOW', self.on_destroy)
        self.playing = 0
        self.score = 0
        self.life = 0
        self.ship = None
        self.root.mainloop()

    def on_destroy(self, e= None):
        self.root.destroy() 

    def rotate_left(self, event=None):
        self.ship.rotate_left(event)

    def rotate_right(self, event=None):
        self.ship.rotate_right(event)

    def fire(self, event = None):
        self.ship.fire(event)

    def speed_up(self, event=None):
        self.ship.speed_up(event)

    def slow_down(self, event=None):
        self.ship.slow_down(event)

    def update_score(self, score):
        # update score on canvas
        self.score += score
        self.canv.itemconfigure(self.canv.find_withtag('score')[0], text='%d' % self.score)

    def decrease_life(self):
        # decrease life count
        if self.life > 0:
            self.life -=1
            self.canv.delete(self.canv.find_withtag('score_ship')[0])
            return True
        else:
            self.canv.itemconfigure(self.canv.find_withtag('game_status')[0], text='GAME OVER')
            self.canv.itemconfigure(self.canv.find_withtag('score')[0], text='')
            self.playing = 0
        return False

    def display_ships(self):
        # create ships to indicate remaining life
        j = 0
        while j < self.life:
            i = j * 25
            scoord = [(40+i, 50), (40+i-15, 50+20),(40+i, 50+15), (40+i+15, 50+20)]
            self.canv.create_polygon(scoord, outline='black', fill='gray40', tags=('score_ship'))
            j+=1

    def resetgame(self, event=None):
        # reset game by removing all asteroids and updating controls
        if self.playing == 0:
            self.playing = 1
            self.score = 0
            self.life = 4
            asteroids = self.canv.find_withtag('Asteroid')
            map(self.canv.delete, asteroids)
            self.ship = Ship(self.canv)
            self.canv.itemconfigure(self.canv.find_withtag('score')[0], text='0')
            self.canv.itemconfigure(self.canv.find_withtag('game_status')[0], text='')
            self.display_ships()

    def _load_objects(self):
        self.canv = Canvas(self.root, highlightthickness=0, offset="40,40", bg='black')
        self.canv.pack(fill='both', expand=True)
        self.ship = None
        self.root.after(1000, self._add_asteroids)
        self.canv.create_text(400,100,anchor=W, font="Purisa", text="  Asteroids\nPlay Game",fill='white', tags="game_status")
        self.canv.create_text(30,30,anchor=W, font="Purisa", text="", tags="score", fill='white')

    def _add_asteroids(self):
        # this function is called repeatedly to add asteroids to canvas
        if len(self.canv.find_withtag('Asteroid')) > 10:
            self.root.after(1000, self._add_asteroids)
            return
        side = random.randint(0, 3) # generate number for one of the four sides
        shape = random.choice([ASTEROID_SMALL, ASTEROID_MEDIUM, ASTEROID_LARGE])
        speed = random.choice(SPEEDS)
        if side == 0:
            x = 10
            y = random.randint(0, self.canv.winfo_height() - 10)
            angle = random.randrange(-90, 90, 10)
            Asteroid(self.canv,  radians(angle),(x,y), shape, speed, self)
        elif side == 1:
            y = 50
            x = random.randint(0, self.canv.winfo_width() - 10)
            angle = random.randrange(0, 180, 10)
            Asteroid(self.canv,  radians(angle),(x,y), shape, speed, self)
        elif side == 2:
            x = self.canv.winfo_width() - 50
            y = random.randint(0, self.canv.winfo_height() - 10)
            angle = random.randrange(90, 270, 10)
            Asteroid(self.canv,  radians(angle),(x,y), shape, speed, self)
        elif side == 3:
            y = self.canv.winfo_height() - 50
            x = random.randint(0, self.canv.winfo_height() - 10)
            angle = random.randrange(180, 360,10)
            Asteroid(self.canv,  radians(angle),(x,y), shape, speed, self)

        self.root.after(1000, self._add_asteroids)
    
if __name__ == '__main__':
    game = Game()

