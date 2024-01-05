import numpy as np

class Array:
    def __init__(self) -> None:
        self.Size = np.array([5, 5])
        self.Pattern = "iso"
        self.Normal = "x"
        self.ElementSpacing = np.array([.5, .5])
        self.Positions = []

    def design(self):
        self.Positions = self.getElementPosition()
        # self.G = self.getPattern()

    def getPattern(self):
        pass

    def getElementPosition(self):
        N = np.prod(self.Size)
        elem_idx = np.arange(1, N + 1)
        pos = self.calcElementPosition(elem_idx, self.Size, self.ElementSpacing, self.Normal)
        return pos

    @staticmethod
    def calcElementPosition(EleIdx, array_sz, elementSpacing, arNr):
        NPerRow = array_sz[1]  # number of elements in each row
        NPerCol = array_sz[0]  # number of elements in each column
        deltaRows = (NPerRow - 1) / 2 + 1  # delta along the row
        deltaCols = (NPerCol - 1) / 2 + 1  # delta along the column

        IdxInRow, IdxInCol = np.unravel_index(EleIdx - 1, array_sz)
        pos2 = (IdxInRow - deltaRows + 1) * elementSpacing[1]
        pos3 = (deltaCols - 1 - IdxInCol) * elementSpacing[0]

        pos = np.zeros((3, EleIdx.size))
        match arNr.lower():
            case 'x':
                pos[1] = pos2
                pos[2] = pos3
            case 'y':
                pos[0] = -pos2
                pos[2] = pos3
            case 'z':
                pos[0] = pos2
                pos[1] = pos3

        return pos

    @staticmethod
    def cosd(angle):
        return np.cos(np.deg2rad(angle))
    
    @staticmethod
    def sind(angle):
        return np.sin(np.deg2rad(angle))