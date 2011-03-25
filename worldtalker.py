# The world talker is how the AI and units talk to the world.
import ai
import ai_exceptions
import copy
import mapobject
import random
import world
import sys

class WorldTalker:
    def __init__(self, world):
        self.__world = world
        self.__world.wt = self
        self.__cached_turn = None
        #self.__eq = world.getQueue()

    def __getStats(self, unit):
        return self.__world.getStats(unit)

    def __getOwner(self, unit):
        if unit.__class__ == mapobject.Unit:
            return self.__getStats(unit).ai_id
        elif unit.__class__ == mapobject.Building:
            return self.__world.buildings[unit].ai_id

    def getOwner(self, unit):
        return self.__getOwner(unit)

    def isAlive(self, unit):
        return self.__world.alive[unit]

    def isCapturing(self, unit):
        return self.__world.capturing[unit]

    def isVisible(self, unit):
        squares = self.getVisibleSquares()
        return unit in squares

    def inRange(self, unit):
        # relies on both sight and bullet range.
        # Find all visible units to this unit.
        self.__getOwner(unit)
        squares = self.getVisibleSquares(unit)
        origin = self.getPosition(unit)
        units = []
        for vunit in self.__world.units:
            square = self.getPosition(vunit)
            if self.__getOwner(vunit) == self.__getOwner(unit):
                continue
#            if self.getPosition(vunit) in squares:
#                print "%s is visible to %s" % (vunit, unit)
            if square in squares and self.__world.map.calcDistance(origin,
                    square) <= self.__world.bulletRange:
                units.append(vunit)
        return units

    # Get functions

    def calcBulletPath(self, unit, square):
        ai_id = self.getID()
        if not unit in self.getVisibleUnits() and not unit in self.getUnits():
            return []
        return self.__world.map.calcBulletPath(self.__world.map.getPosition(unit), square, self.__world.bulletRange)

    def getBulletRange(self):
        return self.__world.bulletRange

    def getCurrentTurn(self):
        return self.__world.getLifeTime()

    def calcDistance(self, unit, square):
        ai_id = self.getID()
        if self.isVisible(unit, ai_id) or unit in self.getUnits():
            unit_square = self.__world.map.getPosition(unit)
            return self.__world.map.calcDistance(unit_square, square)
        else:
            return None

    def getMapSize(self):
        return self.__world.mapSize

    def getPosition(self, unit):
        ai_id = self.getID()
        # Need to make sure the unit is still visible to the guy calling this function, I think.
        position = self.__world.map.getPosition(unit)
        if unit.__class__ == mapobject.Building:
            return position
        elif self.__getOwner(unit) == ai_id:
            return position

        if position in self.getVisibleSquares():
            return position

    def getStats(self, unit):
        ai_id = self.getID()
        stats = copy.copy(self.__world.units[unit])
        stats.ai_id = None
        return stats

    def getTeam(self, unit):
        return self.__world.units[unit].team

    def getBuildings(self):
        ai_id = self.getID()
        buildings = []
        for building in self.__world.buildings:
            if self.__getOwner(building) == ai_id:
                buildings.append(building)

        return buildings

    def getUnits(self):
        ai_id = self.getID()
        units = []
        for unit in self.__world.units:
            if self.__getOwner(unit) == ai_id:
                units.append(unit)

        return units

    def calcUnitPath(self, unit, square):
        ai_id = self.getID()
        if not unit in self.getVisibleUnits() and unit not in self.getUnits():
            return []
        return self.__world.map.calcUnitPath(self.__world.map.getPosition(unit), square)

    # Return all the units that would be hit by a bullet shot at target square.
    # (Assuming they stay still)
    def calcVictims(self, unit, square):
        ai_id = self.getID()
        path = self.__world.map.calcBulletPath(self.__world.map.getPosition(unit), square, self.__world.bulletRange)
        victims = []
        for unit in self.__world.units:
            if self.__world.map.getPosition(unit) in path:
                victims.append(unit)
        return victims

    # If unit is none, return all squares visible to the AI
    # else return only visible squares to the unit
    def getVisibleSquares(self, unit=None):
        if self.__cached_turn < self.getCurrentTurn():
            self.__cached_visible_squares = {}
            self.__cached_turn = self.getCurrentTurn()

        ai_id = self.getID()
        vs_key = unit or ai_id

        if not vs_key in self.__cached_visible_squares:
            if not unit:
                ai_id = ai_id
                squares = set()
                for unit in self.getUnits():
                    stats = self.__getStats(unit)
                    square = self.getPosition(unit)
                    # TODO Properly calculate the sight of the unit.
                    moves = self.__world.map.getLegalMoves(square, stats.sight)
                    squares.update(moves)

                self.__cached_visible_squares[vs_key] = squares
                return squares
            else:
                self.checkOwner(unit)
                stats = self.__getStats(unit)
                square = self.getPosition(unit)
                squares = self.__world.map.getLegalMoves(square, stats.sight)
                self.__cached_visible_squares[vs_key] = squares
        return self.__cached_visible_squares[vs_key]


    def getVisibleBuildings(self, unit=None):
        ai_id = self.getID()
        squares = self.getVisibleSquares(unit)
        buildings = []
        for b in self.__world.buildings.keys():
            if self.__world.map.getPosition(b) in squares:
                buildings.append(b)
        return buildings

    def getVisibleUnits(self, unit=None):
        ai_id = self.getID()
        squares = self.getVisibleSquares(unit)
        units = []
        for unit in self.__world.units:
            if self.__getOwner(unit) == ai_id:
                continue
            if self.__world.map.getPosition(unit) in squares:
                units.append(unit)
        return units

    def getID(self):
        # this function will print out the ai_id of the caller (or his parent, maybe)
        i = 0
        while True:
            try:
                i+=1
                frame = sys._getframe(i)
                f_locals = frame.f_locals
                try:
                    if ai.AI in f_locals['self'].__class__.__bases__:
                        ai_id =  frame.f_locals['self'].ai_id
                        del frame
                        return ai_id
                except KeyError:
                    pass
            finally:
                try:
                    del frame
                except:
                    pass

    # Unit Helper functions
    def checkOwner(self, unit):
        ai_id = self.getID()
        if self.__getOwner(unit) != ai_id:
            raise ai_exceptions.InvalidOwnerException("You don't own this unit")

    def checkAlive(self, unit):
        ai_id = self.getID()
        if not self.__world.alive[unit]:
            raise ai_exceptions.DeadUnitException("This unit is deceased")

    def checkQueue(self, unit):
        for event in self.__world.events:
            if event.getUnit() == unit:
                self.__world.events.remove(event)
                

    # Unit Functions
    def capture(self, unit, square):
        self.checkAlive(unit)
        self.checkOwner(unit)
        self.checkQueue(unit)
        self.__world.createCaptureEvent(unit, square)

    def move(self, unit, square):
        self.checkAlive(unit)
        self.checkOwner(unit)
        self.checkQueue(unit)
        self.__world.createMoveEvent(unit, square)

    def shoot(self, unit, square):
        self.checkAlive(unit)
        self.checkOwner(unit)
        self.checkQueue(unit)
        self.__world.createShootEvent(unit, square, self.__world.bulletRange)


    def calcScore(self, ai_id):
        if ai_id == self.getID():
            return self.__world.calcScore(ai_id)
# vim: set expandtab shiftwidth=4 softtabstop=4 textwidth=79:
