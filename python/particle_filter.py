""" TODO: docstring
"""
from __future__ import (absolute_import, division, print_function)

import random
import math
import bisect
import pymc as pm
import numpy as np
# from sys import sstdin

from world import Map
from database import Database


PARTICLE_COUNT = 3000    # Total number of particles

dist_step_length = pm.Normal('step length error', mu=0, tau=10)
dist_step_heading = pm.Normal('step heading error', mu=0, tau=1/5.)

ROBOT_HAS_COMPASS = False 
# ------------------------------------------------------------------------
# Some utility functions


def add_noise(level, *coords):
    return [x + random.uniform(-level, level) for x in coords]


def add_little_noise(*coords):
    return add_noise(0.02, *coords)


def add_some_noise(*coords):
    return add_noise(1, *coords)

sigma2 = 50 ** 2


def w_gauss(a, b):
    error = a - b
    g = math.e ** -(error ** 2 / (2 * sigma2))
    return g

# ------------------------------------------------------------------------


def compute_mean_point(particles):
    m_x, m_y, m_count = 0, 0, 0
    for p in particles:
        m_count += p.w
        m_x += p.x * p.w
        m_y += p.y * p.w

    if m_count == 0:
        return -1, -1, False

    m_x /= m_count
    m_y /= m_count

    m_count = 0
    for p in particles:
        if world.distance(p.x, p.y, m_x, m_y) < 1:
            m_count += 1

    return m_x, m_y, m_count > PARTICLE_COUNT * 0.95

# ------------------------------------------------------------------------


class WeightedDistribution(object):
    def __init__(self, state):
        accum = 0.0
        self.state = [p for p in state if p.w > 0]
        self.distribution = []
        for x in self.state:
            accum += x.w
            self.distribution.append(accum)

    def pick(self):
        try:
            return self.state[bisect.bisect_left(
                self.distribution, random.uniform(0, 1))]
        except IndexError:
            # Happens when all particles are improbable w=0
            return None

# ------------------------------------------------------------------------


class Particle(object):
    def __init__(self, x, y, heading=None, w=1, noisy=False):
        if heading is None:
            heading = random.uniform(0, 360)
        if noisy:
            x, y, heading = add_some_noise(x, y, heading)

        self.x = x
        self.y = y
        self.h = heading
        self.w = w

    def __repr__(self):
        return "(%f, %f, w=%f)" % (self.x, self.y, self.w)

    @property
    def xy(self):
        return self.x, self.y

    @property
    def xyh(self):
        return self.x, self.y, self.h

    @classmethod
    def create_random(cls, count, maze):
        return [cls(*maze.random_free_place()) for _ in range(0, count)]

    def read_sensor(self, maze):
        """
        Find distance to nearest beacon.
        """
        return maze.distance_to_nearest_beacon(*self.xy)

    def read_all_sensors(self, maze):
        return maze.distance_array_to_beacons(*self.xy)

    def advance_to_coordinates(self, x, y):
        dx = x - self.x
        dy = y - self.y
        bearing = math.atan2(dx, dy)
        self.h = math.degrees(bearing)
        r = math.sqrt(dx * dx + dy * dy)
        return self.advance_by(
            r, noisy=True,
            checker=lambda r, dx, dy:
            not world.segment_is_intersecting_walls(r.x, r.y, r.x+dx, r.y+dy)
            )

    def advance_by(self, speed, checker=None, noisy=False):
        h = self.h
        if noisy:
            speed *= (1 + dist_step_length.random())
            h += dist_step_heading.random()
            # speed, h = add_some_noise(speed, h)
            # h += random.uniform(-3, 3) # needs more noise to disperse better
        r = math.radians(h)
        dx = math.sin(r) * speed
        dy = math.cos(r) * speed
        if checker is None or checker(self, dx, dy):
            # if checker is not None:
            #     print(checker(self, dx, dy))
            self.move_by(dx, dy)
            return True
        return False

    def move_by(self, x, y):
        self.x += x
        self.y += y

# ------------------------------------------------------------------------


class Robot(Particle):
    speed = 10

    def __init__(self, maze):
        super(Robot, self).__init__(*maze.random_free_place(), heading=90)
        self.chose_random_direction()
        self.step_count = 0
        print('Robot initial coordinates', self.x, self.y)
        print(world.is_free(self.x, self.y))

    def chose_random_direction(self):
        heading = random.triangular(0, 180, 360)
        self.h = heading

    def read_sensor(self, maze):
        return add_little_noise(super(Robot, self).read_sensor(maze))[0]

    def read_all_sensors(self, maze):
        return add_little_noise(*super(Robot, self).read_all_sensors(maze))

    def move(self, maze):
        while True:
            self.step_count += 1
            if self.advance_by(
                self.speed, noisy=False,
                checker=lambda r, dx, dy:
                not maze.segment_is_intersecting_walls(
                    r.x, r.y, r.x+dx, r.y+dy)):
                break
            # Bumped into something or too long in same direction,
            # chose random new direction
            # print('self.chose_random_direction()')
            self.chose_random_direction()

# ------------------------------------------------------------------------

world = Map('dfki-2nd-floor.json')
world.draw()

db = Database()

all_loc_docs = db.view_result("all_location_documents_from_reckonme/")
all_loc_docs = all_loc_docs[['2014-02-26']:]

reckonme_location_data = {}

for row in all_loc_docs:
    data = {k: v for k, v in db[row.id].iteritems()}
    if row.key[1] not in reckonme_location_data:
        reckonme_location_data[row.key[1]] = [data]
    else:
        reckonme_location_data[row.key[1]].append(data)

arr = [el['location'] for el in reckonme_location_data[u'6F264452-6B15-41F8-8968-F9D6FA6B0303']]

pixel_array = []

for position in arr:
        meters = world.GPSToAbsoluteXYMeters(
            position['latitude'], position['longitude'])
        pixs = world.XYMetersToPixels(*meters)
        pixs = int(pixs[0]), int(pixs[1])
        pixel_array.append(pixs)



# initial distribution assigns each particle an equal probability
particles = Particle.create_random(PARTICLE_COUNT, world)
robbie = Robot(world)
robbie.x = 246
robbie.y = 110

step_count = 0

for step in pixel_array:
    # print("Step count:", step_count)
    step_count += 1

    # r_d = robbie.read_sensor(world)
    r_d = np.array(robbie.read_all_sensors(world))

    for p in particles:
        if world.is_free(*p.xy):
            # p_d = np.array(p.read_all_sensors(world))
            # error = math.sqrt(sum((r_d - p_d)**2))
            # p.w *= w_gauss(0, error)
            pass
        else:
            p.w = 0

    # ---------- Try to find current best estimate for display ----------
    m_x, m_y, m_confident = compute_mean_point(particles)

    # ---------- Show current state ----------
    # world.show_robot(robbie)
    world.show_particles(particles)
    world.show_mean(m_x, m_y, m_confident)
    # world.show_robot(robbie)

    # ---------- Shuffle particles ----------
    new_particles = []

    # Normalise weights
    nu = sum(p.w for p in particles)
    if nu:
        for p in particles:
            p.w = p.w / nu

    # create a weighted distribution, for fast picking
    dist = WeightedDistribution(particles)

    for old_particle in particles:
        p = dist.pick()
        if p is None:  # No pick b/c all totally improbable
            new_particle = Particle.create_random(1, world)[0]
        else:
            new_particle = Particle(
                p.x, p.y,
                heading=robbie.h if ROBOT_HAS_COMPASS else p.h, noisy=True)
        new_particle.canvas_id = old_particle.canvas_id
        new_particles.append(new_particle)

    particles = new_particles

    # ---------- Move things ----------
    # old_heading = robbie.h
    # robbie.move(world)
    # d_h = robbie.h - old_heading

    for p in particles:
        # p.h += d_h  # in case robot changed heading, swirl particle heading too
        # could_move = p.advance_by(
        #     robbie.speed, noisy=True,
        #     checker=lambda r, dx, dy:
        #     not world.segment_is_intersecting_walls(r.x, r.y, r.x+dx, r.y+dy))
        could_move = p.advance_to_coordinates(step[0], step[1])
        if not could_move:
            p.w = 0
