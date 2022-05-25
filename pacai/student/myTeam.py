import math
from os import stat
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
    
    def generateAllSuccessorStates(self, gameState, index):
        legalActions = gameState.getLegalActions(index)
        rtn = [(gameState.generateSuccessor(index, action), action) for action in legalActions]
        for x in rtn:
            if x[1] == 'Stop':
                rtn.remove(x)
        # if index != 0:
        #     print(0)
        return rtn

    def chooseAction(self, gameState):
        rtn = self.getActionRecur(gameState, 0, -math.inf, math.inf)[1]
        return rtn

    def getActionRecur(self, state, level, alpha, beta):
        depth = 2
        numAgents = state.getNumAgents()
        agentIndex = level % numAgents

        if level >= (depth * numAgents):
            return (self.getScore(state), None)

        successorStates = self.generateAllSuccessorStates(state, agentIndex)
        tmp = self.red
        if len(successorStates) == 0:
            return (self.getScore(state), None)

        if agentIndex in self.getOpponents(state):
            minEval = math.inf
            for successor in successorStates:
                successorEval = self.getActionRecur(successor[0], level + 1, alpha, beta)[0]
                if minEval > successorEval:
                    minEval = successorEval
                    minState = successor
                beta = min(beta, minEval)
                if beta <= alpha:
                    break
            return (minEval, minState[1])
        else:
            maxEval = -math.inf
            for successor in successorStates:
                successorEval = self.getActionRecur(successor[0], level + 1, alpha, beta)[0]
                if maxEval < successorEval:
                    maxEval = successorEval
                    maxState = successor
                alpha = max(alpha, maxEval)
                if beta <= alpha:
                    break
            return (maxEval, maxState[1])


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

