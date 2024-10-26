import PySimpleGUI as psGui
import numpy as np
import sys

from MillEnv import MillEnv
from mcts import State, MonteCarloTreeSearch

if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 7):
    raise Exception("Python 3.7 or later is required for this code.")

class MillDisplayer(object):
    def __init__(self, MillEnvironment: MillEnv = None):
        psGui.theme("dark")
        self.millImage: str = "MühleBrett.png"
        self.blackCheckerImage: str = "Schwarz.png"
        self.whiteCheckerImage: str = "Weiss.png"
        self.millEnv: MillEnv = MillEnv()
        if MillEnvironment is not None:
            self.millEnv = MillEnvironment
        self.ImageIDArray = np.array([])
        self.imageLocations = [(10, 490), (225, 490), (440, 490),
                               (75, 415), (225, 415), (375, 415),
                               (150, 340), (225, 340), (310, 340),
                               (10, 265), (75, 265), (150, 265),
                               (310, 265), (375, 265), (440, 265),
                               (150, 190), (225, 190), (310, 190),
                               (75, 115), (225, 115), (375, 115),
                               (10, 55), (225, 55), (440, 55)]
        self.graph = psGui.Graph(
            canvas_size=(500, 500),
            graph_bottom_left=(0, 0),
            graph_top_right=(500, 500),
        )
        self.statusTextBox = psGui.Text("Player " + self.getPlayerName(self.millEnv.isPlaying) + " is playing",
                                        size=(50, 1))
        self.layout_ = [
            [psGui.Button("Human vs. Human"), psGui.Button("Human vs. Computer"), psGui.Button("Computer vs. Computer")],
            [psGui.Button("Record"), psGui.Button("Pause"), psGui.Button("Save Record"), psGui.Button("Reply")],
            [self.statusTextBox],
            [self.graph],
            [psGui.Button("Close")]]
        self.window = psGui.Window("Nine Men Morris", layout=self.layout_, finalize=True)
        self.window.finalize()
        self.graph.DrawImage(filename=self.millImage, location=(0, 500))
        self.activateClick()
        self.reloadEnv()
        self.recording = False
        self.recorded_moves = []

    def windowsLoop(self):
        while True:
            event, values = self.window.read()
            if event == psGui.WIN_CLOSED or event == 'Close':  # if user closes window or clicks cancel
                break
            elif not event == "":
                self.reset()
        self.window.close()

    def makeMove(self, pos: int) -> bool:
        valid, reward = self.millEnv.makeMove(pos)
        if valid:
            self.reloadEnv()
        return valid

    def reloadEnv(self):
        self.setStatus("Player " + self.getPlayerName(self.millEnv.isPlaying) + " is playing - move needed: " + str(
            self.millEnv.moveNeeded))
        for imageID in self.ImageIDArray:
            self.graph.DeleteFigure(imageID)
        self.ImageIDArray = np.array([])
        for case, location in zip(self.millEnv.getBoard(), self.imageLocations):
            if case == 1:
                self.ImageIDArray = np.append(self.ImageIDArray,
                                              self.graph.DrawImage(filename=self.blackCheckerImage, location=location))
            elif case == -1:
                self.ImageIDArray = np.append(self.ImageIDArray,
                                              self.graph.DrawImage(filename=self.whiteCheckerImage, location=location))
        self.window.refresh()

    def getClicked(self, event) -> int:
        for index, location in enumerate(self.imageLocations):
            x2, y2 = location
            if self.isInArea(event.x, -event.y + 500, x2, y2, 50, 50):
                return index
        return -1

    def setAfterClicked(self, event):
        pos = self.getClicked(event)
        if pos == -1:
            return False
        if self.millEnv.moveNeeded == 2:
            dif = self.millEnv.selected - pos
            if dif == 0:
                return False
            if dif == -1:
                pos = 1
            elif dif == 1:
                pos = 3
            elif dif < 0:
                pos = 2
            elif dif > 0:
                pos = 0
        return self.makeMove(pos)

    def isInArea(self, posX1: int, posY1: int, posX2: int, posY2: int, width: int, height: int) -> bool:
        if posX2 <= posX1 <= posX2 + width:
            if posY2 >= posY1 >= posY2 - height:
                return True
        return False

    def setStatus(self, status: str):
        self.statusTextBox.Update(status)

    def close(self):
        self.window.close()

    def activateClick(self):
        self.graph.TKCanvas.bind("<Button-1>", self.setAfterClicked)

    def deactivateClick(self):
        self.graph.TKCanvas.unbind("<Button-1>")

    def read(self, timout: bool = False):
        return self.window.read(0 if timout else None)

    def reset(self):
        self.millEnv.reset()
        self.reloadEnv()

    def getPlayerName(self, player: int) -> str:
        if player == 1:
            return "black"
        elif player == -1:
            return "white"
        else:
            return "not a player"
        
    def toggleRecording(self):
        self.recording = not self.recording
        if self.recording:
            self.recorded_moves = []

class ModeratedGraphics(object):
    def __init__(self, gamma=0.9, num_sims=250, max_depth=15):
        self.max_depth = max_depth
        self.num_sims = num_sims
        self.gamma = gamma
        self.env = MillEnv()
        self.graphics = MillDisplayer(self.env)
        self.graphics.reloadEnv()
        self.root: State = State(self.env)
        self.mcts = MonteCarloTreeSearch(self.root)
        self.recording = False
        self.recorded_moves = []

    def agentPlay(self):
        self.resetMonteCarlo()
        self.graphics.deactivateClick()
        finished = 0
        while finished == 0:
            self.graphics.reloadEnv()
            pos = self.mcts.best_action(self.gamma, multiplikator=self.num_sims, max_depth=self.max_depth)
            self.graphics.makeMove(pos)
            self.mcts.setNewRoot(State(self.env))
            event, values = self.graphics.read(True)
            if self.eventHandler(event):
                return
            finished = self.env.isFinished()
        self.graphics.reloadEnv()
        if not finished == 2:
            self.graphics.setStatus("player " + self.graphics.getPlayerName(finished) + " won")
            print("Player as won the game")
        else:
            self.graphics.setStatus("The game ended in a draw")

    def playersVSPlayer(self):
        self.graphics.activateClick()
        self.graphics.reset()
        finished = 0
        while finished == 0:
            try:
                event, values = self.graphics.read()
            except BrokenPipeError:
                break
            if self.eventHandler(event):
                return
            self.graphics.reloadEnv()
            finished = self.env.isFinished()
        self.graphics.reloadEnv()
        if not finished == 2:
            self.graphics.setStatus("player " + self.graphics.getPlayerName(finished) + " won")
        else:
            self.graphics.setStatus("The game ended in a draw")
        self.graphics.deactivateClick()

    def playerVSAgent(self):
        self.graphics.activateClick()
        self.resetMonteCarlo()
        finished = 0
        while finished == 0:
            event, values = self.graphics.read(True)
            if self.eventHandler(event):
                return
            if self.env.isPlaying == 1:
                self.graphics.activateClick()
            else:
                self.graphics.deactivateClick()
                self.root = State(self.env)
                self.mcts.setNewRoot(self.root)
                pos = self.mcts.best_action(self.gamma, multiplikator=self.num_sims, max_depth=self.max_depth)
                self.mcts.setNewRoot(State(self.env))
                self.graphics.makeMove(pos)
            #self.graphics.reloadEnv()
            finished = self.env.isFinished()
        self.graphics.reloadEnv()
        if not finished == 2:
            self.graphics.setStatus("player " + self.graphics.getPlayerName(finished) + " won")
        else:
            self.graphics.setStatus("The game ended in a draw")
        self.graphics.deactivateClick()

    def playLoop(self):
        self.graphics.deactivateClick()
        self.playerVSAgent()
        finished = False
        while not finished:
            event, values = self.graphics.read()
            finished = self.eventHandler(event)

    def eventHandler(self, event) -> bool:
        if event == psGui.WIN_CLOSED or event == 'Close':  # if the user closes the window or clicks cancel
            self.graphics.close()
            return True
        elif event == "Computer vs. Computer":
            self.agentPlay()
        elif event == "Human vs. Human":
            self.playersVSPlayer()
        elif event == "Human vs. Computer":
            self.playerVSAgent()
        elif event == "Record":
            self.toggleRecording()
        elif event == "Pause":
            self.pauseRecording()
        elif event == "Save Record":
            self.saveRecordToFile()
        elif event == "Reply":
            self.toggleRecording()
        return False


    def toggleRecording(self):
        self.graphics.toggleRecording()
        self.recording = self.graphics.recording
        if not self.recording:
            self.recorded_moves = []

    def pauseRecording(self):
        self.recording = False

    def makeMove(self, pos: int) -> bool:
        valid, reward = self.millEnv.makeMove(pos)
        if valid and self.recording:
            self.recorded_moves.append(pos)  # Record the move
        if valid:
            self.reloadEnv()
        return valid

    def saveRecordToFile(self, filename="recorded_moves.txt"):
        if not self.recording:
            print("Recording is not active. Please press the 'Record' button during gameplay.")
            return

        if not self.recorded_moves:
            print("No moves recorded.")
            return

        try:
            with open(filename, "w") as file:
                for move in self.recorded_moves:
                    file.write(str(move) + "\n")
            print(f"Recorded moves saved to {filename}.")
        except Exception as e:
            print(f"Error saving recorded moves: {e}")

    def resetMonteCarlo(self):
        self.env.reset()
        self.root = State(self.env)
        self.mcts = MonteCarloTreeSearch(self.root)

if __name__ == '__main__':
    MCGraphics = ModeratedGraphics(gamma=0.9, max_depth=12, num_sims=750)
    MCGraphics.playLoop()