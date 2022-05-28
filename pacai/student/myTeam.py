from pacai.core import distance
from pacai.agents.capture.capture import CaptureAgent
from pacai.util import reflection
# from pacai.agents.capture.offense import OffensiveReflexAgent
# from pacai.agents.capture.defense import DefensiveReflexAgent
from pacai.agents.capture.reflex import ReflexCaptureAgent
from pacai.core.directions import Directions
from pacai.student.multiagents import ReflexAgent


def createTeam(firstIndex, secondIndex, isRed,
        first = 'pacai.agents.capture.dummy.DummyAgent',
        second = 'pacai.agents.capture.dummy.DummyAgent'):
    """
    This function should return a list of two agents that will form the capture team,
    initialized using firstIndex and secondIndex as their agent indexed.
    isRed is True if the red team is being created,
    and will be False if the blue team is being created.
    """

    firstAgent = OffensiveAgent
    secondAgent = DefensiveAgent

    return [
        firstAgent(firstIndex),
        secondAgent(secondIndex),
    ]

class OffensiveAgent(ReflexCaptureAgent):
    def __init__(self, index, **kwargs):
        super().__init__(index)

    def getFeatures(self, gameState, action):
        features = {}
        successor = self.getSuccessor(gameState, action)
        features['successorScore'] = self.getScore(successor)

        # Compute distance to the nearest food.
        foodList = self.getFood(successor).asList()

        # Computer distance to nearest capsule
        capsuleList = self.getCapsules(successor)

        # This should always be True, but better safe than sorry.
        if (len(foodList) > 0):
            myPos = successor.getAgentState(self.index).getPosition()
            minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
            features['distanceToFood'] = minDistance

        # if capsuleList:
        #     myPos = successor.getAgentState(self.index).getPosition()
        #     minDistance = min([self.getMazeDistance(myPos, cap) for cap in capsuleList])
        #     features['distanceToCapsule'] = minDistance

        # compute dist to enemy
        enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        defenders = [a for a in enemies if a.isGhost() and a.getPosition() is not None]
        if (len(defenders) > 0):
            # dists = [distance.manhattan(myPos, a.getPosition()) for a in defenders]
            dists = []
            closestGhost = None
            currentMin = 10000
            for a in defenders:
                distance = self.getMazeDistance(myPos, a.getPosition())
                dists.append(distance)
                # get the ghost object that is closest to Pacman
                if distance < currentMin:
                    currentMin = distance
                    closestGhost = a
            distanceToEnemy = 10
            minDist = min(dists)
            # if ghost is within 5 distance of pacman
            if dists and minDist < 5 and successor.getAgentState(self.index).isPacman():
                distanceToEnemy = minDist

            # if ghosts are scared then go towards them
            # THIS IS NOT WORKING PACMAN STILL RUNS AWAY FROM SCARED GHOSTS and doesnt eat capsules
            # if closestGhost.getScaredTimer() != 0:
            #     distanceToEnemy *= -1

            features['distanceToEnemy'] = distanceToEnemy

        # Discourage stopping
        if (action == Directions.STOP):
            features['stop'] = 1
        
        return features

    def getWeights(self, gameState, action):
        return {
            'successorScore': 100,
            'distanceToFood': -1,
            'distanceToEnemy': 100,
            'stop': -200,
            'distanceToCapsule': 0
        }
    
    def getAction(self, gameState):
        return super().getAction(gameState)


class DefensiveAgent(ReflexCaptureAgent):
    def __init__(self, index, **kwargs):
        super().__init__(index)
    

    def getFeatures(self, gameState, action):
        features = {}
        
        successor = self.getSuccessor(gameState, action)
        myState = successor.getAgentState(self.index)
        myPos = myState.getPosition()

        # Computes whether we're on defense (1) or offense (0).
        features['onDefense'] = 1
        if (myState.isPacman()):
            features['onDefense'] = 0

        # Computes distance to invaders we can see.
        enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        invaders = [a for a in enemies if a.isPacman() and a.getPosition() is not None]
        features['numInvaders'] = len(invaders)
        
        
        if (len(invaders) > 0):
            dists = [(self.getMazeDistance(myPos, a.getPosition()), a) for a in invaders]
            features['invaderDistance'], closestInvader = min(dists)
        # when there are no invaders go the middle of the layout
        else:
            middle = [int(gameState.getInitialLayout().width / 2.3), int(gameState.getInitialLayout().height / 2)]
            while gameState.hasWall(middle[0], middle[1]):
                middle[0] = middle[0] - 1
            middist = self.getMazeDistance(myPos, tuple(middle))
            features['waitmiddle'] = middist

        if (action == Directions.STOP):
            features['stop'] = 1

        rev = Directions.REVERSE[gameState.getAgentState(self.index).getDirection()]
        if (action == rev):
            features['reverse'] = 1
        
        # calculates invaderFoodDistance which is the distance to the 
        # food closest to the closest invader 
        if (len(invaders) > 0):
            foodList = self.getFoodYouAreDefending(successor).asList()

            # This should always be True, but better safe than sorry.
            if (len(foodList) > 0):
                myPos = successor.getAgentState(self.index).getPosition()
                invaderPos = closestInvader.getPosition()
                closestFood = min([(self.getMazeDistance(invaderPos, food), food) for food in foodList])
                # print(self.getMazeDistance(myPos, closestFood[1]))
                features['invaderFoodDistance'] = self.getMazeDistance(myPos, closestFood[1])

        return features

    def getWeights(self, gameState, action):
        return {
            'numInvaders': -1000,
            'onDefense': 100,
            'invaderDistance': -10,
            'stop': -100,
            'reverse': -2,
            'invaderFoodDistance': 0,
            'waitmiddle': -100
        }
    def getAction(self, gameState):
        return super().getAction(gameState)

    


class GeneralAgent(CaptureAgent):
    def __init__(self, index, **kwargs):
        super().__init__(index)

    def chooseAction(self, gameState):  
        return None  

