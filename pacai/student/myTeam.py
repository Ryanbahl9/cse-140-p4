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
        second = 'pacai.agents.capture.dummy.DummyAgent',
        **kwargs):
    """
    This function should return a list of two agents that will form the capture team,
    initialized using firstIndex and secondIndex as their agent indexed.
    isRed is True if the red team is being created,
    and will be False if the blue team is being created.
    """

    firstAgent = QLearningAgent
    secondAgent = DefensiveAgent

    return [
        firstAgent(firstIndex, **kwargs),
        secondAgent(secondIndex, **kwargs),
    ]

class QLearningAgent(CaptureAgent):
    """
        List of Class values:
            self.index              : Index of current agent
            self.red                : Whether or not you're on the red team
            self.agentsOnTeam       : Agent objects controlling you and your teammates
            self.distancer          : Maze distance calculator
            self.observationHistory : A history of observations
            self.timeForComputing   : Time to spend each turn on computing maze distances

        Notes:
            This probably could not be used for two agents 
    """
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

        self.lastAction = None
        self.alpha = float(alpha)
        self.epsilon = float(epsilon)
        self.discountRate = float(gamma)
        self.numTraining = int(numTraining)
        self.weights = {}

    def chooseAction(self, gameState):
        
        self.update(gameState)

        if probability.flipCoin(self.epsilon):
            action = random.choice(gameState.getLegalActions(self.index))
        else:
            action = self.getPolicy(gameState)

        self.lastAction = action
        return action

    def getPolicy(self, gameState):
        max_action = Directions.STOP
        max_q_val = 0
        for action in gameState.getLegalActions(self.index):
            qVal = self.getQValue(gameState, action)
            if qVal > max_q_val or max_action is None:
                max_q_val = qVal
                max_action = action
        return max_action
    
    def getQValue(self, state, action):
        qVal = 0
        features = self.getFeatures(state, action)
        for feature in features:
            featureValue = features[feature]
            weight = self.weights.get(feature, 1)
            qVal += weight * featureValue
        return qVal
    
    def getFeatures(self, gameState, action):
        features = {}
        successor = successor.getAgentState(self.index).getPosition()
        features['successorScore'] = gameState.getScore(successor)

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

    # I think this function is called after the previous getAction() takes affect
    # We might want to call update() here instead of chooseAction()
    # def observationFunction(self, state):
    #     return None

    def update(self, gameState):
        lastAction = self.lastAction
        if not lastAction:
            return
        lastState = self.getPreviousObservation()
        reward = self.getReward(gameState)
        discount = self.discountRate
        qPrimeVal = self.getValue(gameState)
        qVal = self.getQValue(lastState, lastAction)
        
        correction = (reward + discount * qPrimeVal) - qVal

        features = self.getFeatures(lastState, lastAction)
        for feature in features:
            newWeight = self.getWeight(feature) + self.alpha * correction * features[feature]
            self.setWeight(feature, newWeight) 

    # Calculates the reward we got for the previous action
    def getReward(self, gameState):
        """ ----- Notes -----

        This will take some thought:
            In P3 the reward is the change in score after we took the last action.
            
            We can't use this approach here because the score is affected by our opponents and the 
            other agent on our team.

            Some ideas for how to calculate reward for offensive agents:
                - Use the change in amount of food (i.e. add a reward if we eat a food) 
                - Add reward if we eat a power up
            
            I'm not sure how we will calculate rewards for invaders because there is no function 
            to tell if we ate an invader

        """
        # TODO: rewrite this function
        currentObv = self.getCurrentObservation()
        prevObv = self.getPreviousObservation()
        reward = currentObv.getScore() - prevObv.getScore()

    def getWeight(self, feature):
        return self.weights.get(feature, 1)
    
    def setWeight(self, feature, value):
        self.weights[feature] = value




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

