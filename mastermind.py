import requests
import logging
from tinydb import TinyDB, Query
import threading

logging.basicConfig(filename='mastermind.log', level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def inputWithTimeout(prompt, timeout):
    print(prompt, end='', flush=True)
    result = [None]
    timerEvent = threading.Event()
    def getInput():
        result[0] = input()
        timerEvent.set()
    inputThread = threading.Thread(target=getInput)
    inputThread.start()
    timerEvent.wait(timeout)
    if inputThread.is_alive():
        print(f'\nGame over! You\'ve used up all of your time on this round.')
        inputThread.join()
        return None
    return result[0]

class Mastermind:
    def __init__(self, player):
        self.roundCounter = 1
        self.remainingGuess = 10
        self.inputLength = 4
        self.totalRounds = 10
        self.maxRandomDigit = 7
        self.minRandomDigit = 0
        self.inputTimer = 30
        self.baseScore = 100
        self.currentScore = 0
        self.roundScore = 0
        self.player = player
        self.winningCombo = self.generateWinningCombo()
    
    def generateWinningCombo(self):
        randomdotorgResponse = requests.get("https://www.random.org/integers/", params={'num':self.inputLength, 'min':self.minRandomDigit, 'max':self.maxRandomDigit, 'col':1, 'base':10, 'format':'plain', 'rnd':'new'})
        winningValue = randomdotorgResponse.text
        joinedWinningValue = ''.join(winningValue.split())
        logging.info(f'Winning number generated: {joinedWinningValue}')
        return joinedWinningValue
    
    def playGame(self):
        while True:
            if self.roundCounter == 1:
                userGuess = inputWithTimeout(f'Welcome to Mastermind! You are on Round {self.roundCounter} with {self.remainingGuess} remaining tries. Please guess the {self.inputLength} digit combination with numbers between {self.minRandomDigit} and {self.maxRandomDigit}. You have {self.inputTimer} seconds to guess: ', self.inputTimer)
                logging.info(f'Users guess: {userGuess}')
                if not userGuess:
                    self.handleTimeout()
                    self.handlePlayAgain()
                    break
            elif self.roundCounter <= self.totalRounds and self.roundCounter != 1:
                userGuess = inputWithTimeout(f'You are on Round {self.roundCounter} with {self.remainingGuess} remaining tries. Please guess the {self.inputLength} digit combination with numbers between {self.minRandomDigit} and {self.maxRandomDigit}. You have {self.inputTimer} seconds to guess: ', self.inputTimer)
                logging.info(f'Users guess: {userGuess}')
                if not userGuess:
                    self.handleTimeout()
                    self.handlePlayAgain()
                    break
            else:
                print('Game over! You\'ve used up all your tries.\n')
                self.player.updatePlayerData()
                self.handlePlayAgain()
                break
                    
            if self.checkRequirements(userGuess):
                print(f'Please input a {self.inputLength} digit number between 0 and {self.maxRandomDigit}.\n')
                logging.info(f'Please input a {self.inputLength} digit number between 0 and {self.maxRandomDigit}.\n')
                continue
            else:
                numOfMatching = self.matchingNumbers(userGuess)
                numOfIndices = self.matchingIndices(userGuess)

                if numOfMatching == 0 and numOfIndices == 0:
                    print('All are incorrect. Please try again.\n')
                    logging.info('Computer response: All are incorrect. Please try again.\n')
                    self.roundCounter += 1
                    self.remainingGuess -= 1
                    continue
                elif numOfMatching == self.inputLength and numOfIndices == self.inputLength:
                    self.win()
                    break
                elif numOfMatching > 0 or numOfIndices > 0:
                    print(f'{numOfMatching} correct number(s) and {numOfIndices} correct location(s).\n')
                    logging.info(f'Computer response: {numOfMatching} correct number(s) and {numOfIndices} correct location(s).\n')
                    self.roundCounter += 1
                    self.remainingGuess -= 1
                    continue

    def checkRequirements(self, userGuess):
        return len(userGuess) != self.inputLength or not userGuess.isdigit() or any(char in userGuess for char in ['8','9'])
    
    def win(self):
        self.currentScore += self.baseScore
        self.roundScore += self.scoring(self.currentScore)
        self.handleLeveling(self.roundScore)
        self.player.highestScore = max(self.player.highestScore, self.scoring(self.currentScore))
        self.player.gamesWon += 1
        self.player.winRate = round((self.player.gamesWon / self.player.gamesPlayed) * 100)
        print(f'Congratulations, you have guessed the combination! Your score is: {self.roundScore}')
        print(f'Your current XP is {self.player.currentXP}/{self.player.xpToNextLevel}\n')
        print(f'Your current win rate is: {self.player.winRate}%\n')
        logging.info(f'Computer response: Congratulations, you have guessed the combination! Your score is: {self.roundScore}')
        logging.info(f'Your current XP is {self.player.currentXP}/{self.player.xpToNextLevel}\n')
        logging.info(f'Your current win rate is: {self.player.winRate}%\n')
        if self.player.highestScore >= self.roundScore:
            print(f'Wow! You\'ve set a new high score: {self.player.highestScore}')
            logging.info(f'Computer response: Wow! You\'ve set a new high score: {self.player.highestScore}')
        self.player.updatePlayerData()
        self.handlePlayAgain()
    
    def matchingNumbers(self, userInput):
        counter = 0
        seen = set()
        for num in str(self.winningCombo):
            if num in userInput and num not in seen:
                counter += min(userInput.count(num), str(self.winningCombo).count(num))
                seen.add(num)
        return counter
    
    def matchingIndices(self, userInput):
        counter = 0
        for i in range(len(str(self.winningCombo))):
            if str(self.winningCombo)[i] == userInput[i]:
                counter += 1
        return counter
    
    def handlePlayAgain(self):
        while True:
            userInput = input('Would you like to play again? (y/n): ')
            if userInput == 'y':
                self.player.gamesPlayed += 1
                self.__init__(self.player)
                self.playGame()
                break
            else:
                print('Thanks for playing!')
                break
    
    def handleLeveling(self, roundScore):
        if self.player.currentXP + roundScore < self.player.xpToNextLevel:
            self.player.currentXP += roundScore

        elif self.player.currentXP + roundScore >= self.player.xpToNextLevel:
            remainderXP = self.player.xpToNextLevel - self.player.currentXP
            self.player.currentXP += remainderXP
            if self.player.currentXP == self.player.xpToNextLevel:
                self.player.currentLevel += 1
                print(f'Congratulations! You are now Level {self.player.currentLevel}')
                logging.info(f'Computer response: Congratulations! You are now Level {self.player.currentLevel}')
                self.player.xpToNextLevel = self.player.xpToNextLevel * 1.5
                self.player.currentXP = 0
                self.player.currentXP = roundScore - remainderXP
    
    def handleTimeout(self):
        self.player.updatePlayerData()
    
    def difficultyMultiplier(self, currentScore):
        return round(currentScore * 1)
    
    def roundMultiplier(self, currentScore, currentRound):
        roundToMultiplier = {1:2, 2:1.9, 3:1.8, 4:1.7, 5:1.6, 6:1.5, 7:1.4, 8:1.3, 9:1.2, 10:1.1}
        return round(currentScore * roundToMultiplier[currentRound])

    def scoring(self, currentScore):
        return self.difficultyMultiplier(currentScore) + self.roundMultiplier(currentScore, self.roundCounter)


class EasyPeasyDifficulty(Mastermind):
    def __init__(self, player):
        super().__init__(player)
        self.maxRandomDigit = 5
    
    def checkRequirements(self, userGuess):
        return len(userGuess) != self.inputLength or not userGuess.isdigit() or any(char in userGuess for char in ['6','7','8','9'])
    
    def difficultyMultiplier(self, currentScore):
        return currentScore * 0.5
    
class NormalDifficulty(Mastermind):
    def __init__(self, player):
        super().__init__(player)

class HardDifficulty(Mastermind):
    def __init__(self, player):
        self.roundCounter = 1
        self.remainingGuess = 10
        self.inputLength = 6
        self.totalRounds = 10
        self.maxRandomDigit = 9
        self.minRandomDigit = 0
        self.inputTimer = 30
        self.baseScore = 100
        self.currentScore = 0
        self.roundScore = 0
        self.player = player
        self.winningCombo = self.generateWinningCombo()
    
    def checkRequirements(self, userGuess):
        return len(userGuess) != self.inputLength or not userGuess.isdigit()
    
    def difficultyMultiplier(self, currentScore):
        return currentScore * 2

class ImpossibruDifficulty(Mastermind):
    def __init__(self, player):
        self.roundCounter = 1
        self.remainingGuess = 5
        self.inputLength = 10
        self.totalRounds = 5
        self.maxRandomDigit = 9
        self.minRandomDigit = 0
        self.inputTimer = 30
        self.baseScore = 100
        self.currentScore = 0
        self.roundScore = 0
        self.player = player
        self.winningCombo = self.generateWinningCombo()
    
    def checkRequirements(self, userGuess):
        return len(userGuess) != self.inputLength or not userGuess.isdigit()
    
    def difficultyMultiplier(self, currentScore):
        return currentScore * 4


class Player:
    def __init__(self):
        self.db = TinyDB('./db.json')
        self.playerTable = self.db.table('player')
        self.username = None
        self.loggedIn = False
    
    def createPlayer(self):
        while True:
            username = input('Please enter your username: ')
            existingUserCheck = self.playerTable.search(Query().user==username)
            if existingUserCheck:
                print('That user already exists! Please try another username or log in if that\'s your username.')
                continue
            elif username:
                self.username = username
                password = input('Please enter your password: ')
                if password:
                    self.playerTable.insert({'user':username, 'password':password, 'currentLevel':1, 'xpToNextLevel':1000, 'currentXP':0, 'highestScore':0, 'gamesWon':0, 'gamesPlayed':0, 'winRate':0})
                    self.loggedIn = True
                    self.loadPlayerData()
                    print('Thanks for joining! You are now logged in.')
                    break
                else:
                    print('Please input a password!')
            else:
                print('Please input a username!')

    def logPlayerIn(self):
        if not self.playerTable:
            self.createPlayer()
        else:
            while True:
                username = input('Please enter your username: ')
                if not self.playerTable.search(Query().user==username):
                    print('That username doesn\'t exist. Please try again.')
                    continue
                password = input('Please enter your password: ')
                if password == self.playerTable.search(Query().user==username)[0]['password']:
                    self.username = username
                    self.loggedIn = True
                    self.loadPlayerData()
                    print('You have successfully logged in.')
                    break
                else:
                    print('Incorrect password. Please try again.')
                    continue
    
    def loadPlayerData(self):
        self.highestScore = self.playerTable.search(Query().user==self.username)[0]['highestScore']
        self.currentLevel = self.playerTable.search(Query().user==self.username)[0]['currentLevel']
        self.currentXP = self.playerTable.search(Query().user==self.username)[0]['currentXP']
        self.xpToNextLevel = self.playerTable.search(Query().user==self.username)[0]['xpToNextLevel']
        self.gamesWon = self.playerTable.search(Query().user==self.username)[0]['gamesWon']
        self.gamesPlayed = self.playerTable.search(Query().user==self.username)[0]['gamesPlayed']
        self.winRate = self.playerTable.search(Query().user==self.username)[0]['winRate']

    def updatePlayerData(self):
        self.playerTable.update({'highestScore':self.highestScore}, Query().user==self.username)
        self.playerTable.update({'currentLevel':self.currentLevel}, Query().user==self.username)
        self.playerTable.update({'currentXP':self.currentXP}, Query().user==self.username)
        self.playerTable.update({'xpToNextLevel':self.xpToNextLevel}, Query().user==self.username)
        self.playerTable.update({'gamesWon':self.gamesWon}, Query().user==self.username)
        self.playerTable.update({'gamesPlayed':self.gamesPlayed}, Query().user==self.username)
        self.playerTable.update({'winRate':self.winRate}, Query().user==self.username)


def enterGame(player):
    while True:
        gameDifficultyPicker = input("Welcome to Mastermind! Please select difficulty: EasyPeasy, Normal, Hard, IMPOSSIBRU: ")
        if gameDifficultyPicker == 'EasyPeasy' or gameDifficultyPicker == 'easypeasy':
            game = EasyPeasyDifficulty(player)
            player.gamesPlayed += 1
            game.playGame()
            break
        elif gameDifficultyPicker == 'Normal' or gameDifficultyPicker == 'normal':
            game = NormalDifficulty(player)
            player.gamesPlayed += 1
            game.playGame()
            break
        elif gameDifficultyPicker == 'Hard' or gameDifficultyPicker == 'hard':
            game = HardDifficulty(player)
            player.gamesPlayed += 1
            game.playGame()
            break
        elif gameDifficultyPicker == 'IMPOSSIBRU' or gameDifficultyPicker == 'impossibru':
            game = ImpossibruDifficulty(player)
            player.gamesPlayed += 1
            game.playGame()
            break 
        else:
            print('Please type "EasyPeasy", "Normal", "Hard", or "IMPOSSIBRU" to select a game mode.')
            continue

def main():
    while True:
        returningOrNew = input('Welcome to Mastermind! Are you a new or returning player? (new/returning): ')
        if returningOrNew == 'new':
            player = Player()
            player.createPlayer()
            enterGame(player)
            break

        elif returningOrNew == 'returning':
            player = Player()
            player.logPlayerIn()
            enterGame(player)
            break

        else:
            print('Invalid response. Please enter "new" or "returning."')
            continue
    
main()
