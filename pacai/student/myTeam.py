from pacai.agents.capture.capture import CaptureAgent
from pacai.util import reflection
# from pacai.agents.capture.offense import OffensiveReflexAgent
# from pacai.agents.capture.defense import DefensiveReflexAgent
from pacai.agents.capture.reflex import ReflexCaptureAgent
from pacai.core.directions import Directions
from pacai.student.multiagents import ReflexAgent

# For Q-Learning
import random
from pacai.util import probability



def createTeam(firstIndex, secondIndex, isRed,
        first = 'pacai.agents.capture.dummy.DummyAgent',
        second = 'pacai.agents.capture.dummy.DummyAgent'):
    """
    This function should return a list of two agents that will form the capture team,
    initialized using firstIndex and secondIndex as their agent indexed.
    isRed is True if the red team is being created,
    and will be False if the blue team is being created.
    """

    firstAgent = QLearningAgent
    secondAgent = DefensiveAgent

    return [
        firstAgent(firstIndex),
        secondAgent(secondIndex),
    ]

class QLearningAgent(CaptureAgent):
    def __init__(self, index, alpha = 1.0, epsilon = 0.05,
            gamma = 0.8, numTraining = 10, **kwargs):
        """
        Args:
            alpha: The learning rate.
            epsilon: The exploration rate.
            gamma: The discount factor.
            numTraining: The number of training episodes.
        """
        super().__init__(index, **kwargs)

        self.alpha = float(alpha)
        self.epsilon = float(epsilon)
        self.discountRate = float(gamma)
        self.numTraining = int(numTraining)


    # def chooseAction(self, gameState):
    #     if probability.flipCoin(self.getEpsilon()):
    #         return random.choice(self.getLegalActions(gameState))
    #     return self.getPolicy(gameState)



class OffensiveAgent(ReflexCaptureAgent):
    def __init__(self, index, **kwargs):
        super().__init__(index)

    def getFeatures(self, gameState, action):
        features = {}
        successor = self.getSuccessor(gameState, action)
        features['successorScore'] = self.getScore(successor)

        # Compute distance to the nearest food.
        foodList = self.getFood(successor).asList()

        # This should always be True, but better safe than sorry.
        if (len(foodList) > 0):
            myPos = successor.getAgentState(self.index).getPosition()
            minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
            features['distanceToFood'] = minDistance

        # compute dist to enemy
        enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        defenders = [a for a in enemies if a.isGhost() and a.getPosition() is not None]
        if (len(defenders) > 0):
            # dists = [distance.manhattan(myPos, a.getPosition()) for a in defenders]
            dists = [self.getMazeDistance(myPos, a.getPosition()) for a in defenders]
            minDist = min(dists)
            if (minDist < 3):
                features['distanceToEnemy'] = min(dists)
            else:
                features['distanceToEnemy'] = 0
        
        return features

    def getWeights(self, gameState, action):
        return {
            'successorScore': 100,
            'distanceToFood': -1,
            'distanceToEnemy': -10,
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
            'invaderFoodDistance': 0
        }
    def getAction(self, gameState):
        return super().getAction(gameState)

    


class GeneralAgent(CaptureAgent):
    def __init__(self, index, **kwargs):
        super().__init__(index)

    def chooseAction(self, gameState):  
        return None  

