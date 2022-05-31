import random
from pacai.core import distance
from pacai.agents.capture.capture import CaptureAgent
from pacai.util import reflection
# from pacai.agents.capture.offense import OffensiveReflexAgent
# from pacai.agents.capture.defense import DefensiveReflexAgent
from pacai.agents.capture.reflex import ReflexCaptureAgent
from pacai.core.directions import Directions
from pacai.student.multiagents import ReflexAgent
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

        # Compute distance to nearest capsule
        capsuleList = self.getCapsules(successor)
        oldCapsuleList = self.getCapsules(gameState)

        # Get own position 
        myPos = successor.getAgentState(self.index).getPosition()

        # Add capsule as food
        foodList.extend(capsuleList)

        # reward PacMan for getting close to and eating a capsule
        if oldCapsuleList:
            minDist = min([self.getMazeDistance(myPos, capsule) for capsule in oldCapsuleList])
            features['eatCapsule'] = minDist

        if len(capsuleList) < len(oldCapsuleList):
            features['ateCapsule'] = 10

        # This should always be True, but better safe than sorry.
        if (len(foodList) > 0):
            myPos = successor.getAgentState(self.index).getPosition()
            minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
            features['distanceToFood'] = minDistance

        # if capsuleList:
        #     myPos = successor.getAgentState(self.index).getPosition()
        #     minDistance = min([self.getMazeDistance(myPos, cap) for cap in capsuleList])
        #     features['distanceToCapsule'] = minDistance

        # if (len(foodList) > 0):
        #     if capsuleList:
        #         myPos = successor.getAgentState(self.index).getPosition()
        #         minDistance_f = min([self.getMazeDistance(myPos, cap) for cap in capsuleList])
        #         minDistance_c = min([self.getMazeDistance(myPos, food) for food in foodList])
        #         if minDistance_f > minDistance_c:
        #             features['distanceToFood'] = minDistance_f
        #             features['distanceToCapsule'] = -1000000
        #         else:
        #             features['distanceToFood'] = -100000000000
        #             features['distanceToCapsule'] = minDistance_c

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
            if closestGhost.isScared():
                distanceToEnemy *= -.0

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
            'distanceToCapsule': 0,
            'eatCapsule': -2,
            'ateCapsule': 100
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
            red = gameState.getRedTeamIndices() == self.getTeam(gameState)
            if red:
                modifier = 2.3
            else:
                modifier = 1.7
            middle = [int(gameState.getInitialLayout().width / modifier), int(gameState.getInitialLayout().height / 2)]
            while gameState.hasWall(middle[0], middle[1]):
                if red:
                    middle[0] = middle[0] - 1
                else:
                    middle[0] = middle[0] + 1
            midDist = self.getMazeDistance(myPos, tuple(middle))
            features['waitMiddle'] = midDist

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
            'waitMiddle': -100
        }
    def getAction(self, gameState):
        return super().getAction(gameState)

    


class GeneralAgent(CaptureAgent):
    def __init__(self, index, **kwargs):
        super().__init__(index)

    def chooseAction(self, gameState):  
        return None  

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
        successor = self.getSuccessor(gameState, action)
        features['successorScore'] = self.getScore(successor)

        # Compute distance to the nearest food.
        foodList = self.getFood(successor).asList()

        # Compute distance to nearest capsule
        capsuleList = self.getCapsules(successor)
        oldCapsuleList = self.getCapsules(gameState)

        # Get own position 
        myPos = successor.getAgentState(self.index).getPosition()

        # Add capsule as food
        foodList.extend(capsuleList)

        # reward PacMan for getting close to and eating a capsule
        if oldCapsuleList:
            minDist = min([self.getMazeDistance(myPos, capsule) for capsule in oldCapsuleList])
            features['eatCapsule'] = minDist

        if len(capsuleList) < len(oldCapsuleList):
            features['ateCapsule'] = 10

        # This should always be True, but better safe than sorry.
        if (len(foodList) > 0):
            myPos = successor.getAgentState(self.index).getPosition()
            minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
            features['distanceToFood'] = minDistance

        # if capsuleList:
        #     myPos = successor.getAgentState(self.index).getPosition()
        #     minDistance = min([self.getMazeDistance(myPos, cap) for cap in capsuleList])
        #     features['distanceToCapsule'] = minDistance

        # if (len(foodList) > 0):
        #     if capsuleList:
        #         myPos = successor.getAgentState(self.index).getPosition()
        #         minDistance_f = min([self.getMazeDistance(myPos, cap) for cap in capsuleList])
        #         minDistance_c = min([self.getMazeDistance(myPos, food) for food in foodList])
        #         if minDistance_f > minDistance_c:
        #             features['distanceToFood'] = minDistance_f
        #             features['distanceToCapsule'] = -1000000
        #         else:
        #             features['distanceToFood'] = -100000000000
        #             features['distanceToCapsule'] = minDistance_c

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
            if closestGhost.isScared():
                distanceToEnemy *= -.0

            features['distanceToEnemy'] = distanceToEnemy

        # Discourage stopping
        if (action == Directions.STOP):
            features['stop'] = 1
        
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
        if feature in self.weights:
            return self.weights.get(feature)
        initialWeights = {
            'successorScore': 100,
            'distanceToFood': -1,
            'distanceToEnemy': 100,
            'stop': -200,
            'distanceToCapsule': 0,
            'eatCapsule': -2,
            'ateCapsule': 100
        }
        return initialWeights.get(feature, 1)

    def setWeight(self, feature, value):
        self.weights[feature] = value

