import os
from typing import Any
import numpy as np
import inspect
from glob import glob
from RayData.Antenna import Antenna

class RayData:

    def __init__(self, Input=None):
            self.Input = Input
            self.Path = self.__find_calling_folder(Input)
            self.Nsubcarriers = []
            self.Folders = []
            self._CurrentFolder = []
            self.__Antenna = []
            self.__data_extracted = False
            self.__folder_changed = False

    @classmethod
    def __find_calling_folder(cls, Input):
            stack = inspect.stack()
            calling_context = next(context for context in stack if context.filename != __file__)
            path = os.path.split(calling_context.filename)[0]
            if Input == None:
                path = calling_context
            else:
                path = Input
            return path

    # getter/setter for current folder
    @property
    def CurrentFolder(self):
        return self._CurrentFolder
    
    def Frequency(self, antenna):
        return self.__Antenna[antenna].Frequency
    
    @CurrentFolder.setter
    def CurrentFolder(self, value):
        self._CurrentFolder = value
        self.__folder_changed = True

    def set_BW(self, antenna, value):
        self.__Antenna[antenna]._BandWidth = value

    def get_BW(self, antenna):
        return self.__Antenna[antenna]._BandWidth

    def __getattribute__(self, item):
        if item in ['get_CIR', 'get_TxPos', 'get_RxPos', 'get_DataInfo', 'Frequency'] and self.__data_extracted and self.__folder_changed:
            raise ValueError("The current folder has changed. Consider read again or change to the initial folder")
        else:
            return object.__getattribute__(self, item)

    def findfolders(self):
        folders_list = []
        for i, (curr_path, dirnames, file_names) in enumerate(os.walk(self.Path)):
            #print("i = {}, File: {}, Dir: {}, Filename: {}".format(i, curr_path, dirnames, file_names))
            if not(i):
                folders_list = dirnames
        self.Folders = folders_list
        self._CurrentFolder = folders_list[0]
             
    def read(self):
        folder = ''.join([self.Path, '/', self.CurrentFolder])
        self.__Antenna = RayData.extract_folder(folder)
        self.__data_extracted = True
        self.__folder_changed = False

    def get_CIR(self, antenna=0, plane=0, snapshot=0, polarization='HH'):
        h, tau, AoA, EoA, AoD, EoD = [], [], [], [], [], []
        for curr_path in range(len(self.__Antenna[antenna].Planes[plane][snapshot].Path)):
            AoA.append(self.__Antenna[antenna].Planes[plane][snapshot].Path[curr_path].AoA)
            EoA.append(self.__Antenna[antenna].Planes[plane][snapshot].Path[curr_path].EoA)
            AoD.append(self.__Antenna[antenna].Planes[plane][snapshot].Path[curr_path].AoD)
            EoD.append(self.__Antenna[antenna].Planes[plane][snapshot].Path[curr_path].EoD)
            tau.append(self.__Antenna[antenna].Planes[plane][snapshot].Path[curr_path].Delay)
            match polarization:
                case 'HH':
                    h.append(self.__Antenna[antenna].Planes[plane][snapshot].Path[curr_path].H_hh)
                case 'HV':
                    h.append(self.__Antenna[antenna].Planes[plane][snapshot].Path[curr_path].H_hv)
                case 'VH':
                    h.append(self.__Antenna[antenna].Planes[plane][snapshot].Path[curr_path].H_vh)
                case 'VV':
                    h.append(self.__Antenna[antenna].Planes[plane][snapshot].Path[curr_path].H_vv)

        return np.array(h), np.array(tau), np.array(AoA), np.array(EoA), np.array(AoD), np.array(EoD)
        
    def get_TxPos(self, antenna=0, snapshot=0):
        return self.__Antenna[antenna].TxPos[snapshot]
    
    def get_RxPos(self, plane=0, snapshot=0):
        return self.__Antenna[0].Planes[plane][snapshot].RxPos
    
    def get_DataInfo(self, antenna=0, nrxpoints=True, frequency=True, VERBOSE=1):

        # Data info
        if nrxpoints and frequency and type(antenna) is list: # Multiple antennas, Rx points, Snapshots
            n_rx_points_per_ant = []
            n_snaps_per_ant = []
            for i in range(len(self.__Antenna)):
                if VERBOSE > 0:
                    print("""antenna #{},
                        frequency = {},
                        number of receiving points = {}, 
                        number of snapshots = {}""".format(i, self.__Antenna[i].Frequency, self.__Antenna[i].planes_counter, self.__Antenna[i].curr_tStep))
                n_rx_points_per_ant.append(len(self.__Antenna[i].planes_counter))
                n_snaps_per_ant.append(self.__Antenna[i].curr_tStep)
            return len(self.__Antenna), n_rx_points_per_ant, n_snaps_per_ant
        elif nrxpoints and frequency and type(antenna) in (int, float):
            if VERBOSE > 0:
                print("""antenna #{},
                        frequency = {},
                        number of receiving points = {}, 
                        number of snapshots = {}""".format(antenna, self.__Antenna[antenna].Frequency,
                                                                                        self.__Antenna[antenna].planes_counter, self.__Antenna[antenna].curr_tStep))
            return self.__Antenna[antenna].planes_counter, self.__Antenna[antenna].curr_tStep

    @staticmethod
    def extract_folder(folder):
         Antenna_list = []
         # find # of antenna files (*str_files)
         # create # antenna class instances in for loop
         # each class scans its file and get list of "Plane" 
         for file in os.listdir(folder):

            if file.endswith(".str"):
                if os.path.getsize(os.path.join(folder, file)) == 0:
                    print("{} is empty!".format(file))
                    continue
                print(file)
                antenna = Antenna(os.path.join(folder, file))
                antenna.scan_antenna()
                Antenna_list.append(antenna)
                return Antenna_list
                

        

    
    