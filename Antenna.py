import numpy as np
import os

class Antenna:
    def __init__(self, str_file):
        self.TxPos = []
        self.Planes = []
        self.Frequency = []
        self.BandWidth = []
        self.__File = str_file
        self.DopplerAnalysis = False
        self.curr_tStep = 0
        self.planes_counter = 0

    def scan_antenna(self):
        FILE = os.path.join(self.__File)
        fd = open(FILE,'r')
        antenna_prop = 0
        tx_pos = 0
        rx_data_scanning,scanning_plane,scanning_point = False, False, False
        planes_list = [] # Outer container of planes [] with size n_planes_total x 1
        planes_time_steps = [] # Inner container of planes [] with size n_time_steps x 1
        for line in fd:

            # Antenna properties reading
            if 'Transmitter / antenna properties' in line:
                antenna_prop = 1

            if antenna_prop and 'ANTENNA' in line:
                line = line.replace('ANTENNA', '')
                line = line.replace('\n', '')
                tx_pos = [np.array(line.split()).astype(np.float64)]
                antenna_prop = 0
                self.TxPos = tx_pos

            if 'FREQUENCY' in line:
                line = line.replace('FREQUENCY', '')
                line = line.replace('\n', '')
                freq = np.array(line).astype(np.float64)
                self.Frequency = freq

            if 'ANTENNA_TIME_STEP' in line:
                self.DopplerAnalysis = True
                line = line.replace('ANTENNA_TIME_STEP', '')
                line = line.replace('\n', '')
                new_tx_pos = np.array(line.split()).astype(np.float64)
                tx_pos = np.append(tx_pos, [new_tx_pos], axis=0)
                self.TxPos = tx_pos

            # Only prediction planes (not area)
            if 'Prediction Point' in line and not(rx_data_scanning):
                rx_data_scanning = True
                self.planes_counter += 1
            elif 'Prediction Point' in line and rx_data_scanning:
                self.planes_counter += 1
                planes_list.append(planes_time_steps)

            # This is time variant:
            if 'NEW_TIME_STEP' in line and rx_data_scanning:
                self.curr_tStep += 1
                if scanning_plane:
                    planes_time_steps.append(plane)

            # This is for prediction Points scanning
            if 'POINT_PLANE' in line and not(scanning_plane):                 # first point creation
                scanning_plane = True
                plane = self.Plane(line, self)
                plane.scan_plane()
            elif 'POINT_PLANE' in line and scanning_plane:                  # next point creation
                planes_time_steps.append(plane)
                plane = self.Plane(line, self)
                plane.scan_plane()

            # This is for Area scanning:
            if 'POINT' in line and not ('Syntax of' in line) and not('_PLANE' in line) and not('_PATH' in line) and not('coordinate' in line) and not(scanning_point):
                scanning_point = True
                self.planes_counter += 1
                plane = self.Plane(line, self)
                plane.scan_plane()
            elif 'POINT' in line and not ('Syntax of' in line) and not('_PLANE' in line) and not('_PATH' in line) and not('coordinate' in line) and scanning_point:
                planes_time_steps.append(plane)
                planes_list.append(planes_time_steps)
                self.planes_counter += 1
                plane = self.Plane(line, self)
                plane.scan_plane()
                planes_time_steps = []

            if 'PATH' in line and (scanning_plane or scanning_point):
                plane.create_path(line)

        fd.close()
        planes_time_steps.append(plane)
        planes_list.append(planes_time_steps)
        self.Planes = planes_list



    class Plane:
        def __init__(self, line, antenna):
            self.RxPos = []
            self.Path = []
            self._Antenna = antenna
            self.__Line = line
            self.PixelId = []

        def scan_plane(self):
            line = self.__Line
            if 'POINT_PLANE' in line:
                line = line.replace('POINT_PLANE', '')
            else:
                line = line.replace('POINT', '')
            line = line.replace('\n', '')
            plane_info = np.array(line.split())
            rx_pos = plane_info[:3].astype(np.float64)
            self.RxPos = rx_pos

        def create_path(self, line):
            ray = self.Ray(line, self)
            ray.scan_path()
            self.Path.append(ray)

        class Ray:
            def __init__(self, line, plane):
                self.Delay = []
                self.FieldStrength = []
                self.N_interactions = []
                self.AoD,self.EoD,self.AoA,self.EoA = [], [], [], []
                self.H_hh,self.H_hv,self.H_vh,self.H_vv = [], [], [], []
                self.__Line = line
                self.__Plane = plane
                self._Antenna = plane._Antenna

            def scan_path(self):
                if 'PATH' in self.__Line:
                    line = self.__Line
                    line = line.replace('PATH', '')
                    line = line.replace('\n', '')
                    path_info = np.array(line.split())
                    self.Delay = path_info[0].astype(np.float64) * 10**-9
                    self.FieldStrength = path_info[1].astype(np.float64)
                    self.Type = path_info[2].astype(np.float64)
                    self.N_interactions = path_info[3].astype(int)
                    self.curr_path = path_info[5].astype(int)
                    if self._Antenna.DopplerAnalysis:
                        self.Doppler = path_info[6].astype(np.float64)
                        offset_doppler = 1
                    else:
                        offset_doppler = 0

                    if self.N_interactions >= 1:
                        for curr_interaction in range(self.N_interactions):
                            offset = 6 * curr_interaction + offset_doppler
                            # TODO: interaction information
                            xyz = path_info[6+offset : 9+offset].astype(np.float64)
                            if curr_interaction == 0:
                                rx_xyz_first = xyz
                        rx_xyz_last = xyz
                        xyz_DoA = rx_xyz_last - self.__Plane.RxPos
                        xyz_DoD = rx_xyz_first - self._Antenna.TxPos[self._Antenna.curr_tStep]
                        self.H_vv = path_info[12 + offset].astype(complex) + 1j*path_info[13 + offset].astype(complex)
                        self.H_vh = path_info[14 + offset].astype(complex) + 1j*path_info[15 + offset].astype(complex)
                        self.H_hv = path_info[16 + offset].astype(complex) + 1j*path_info[17 + offset].astype(complex)
                        self.H_hh = path_info[18 + offset].astype(complex) + 1j*path_info[19 + offset].astype(complex)
                    #elif self.N_interactions >= 1:  
                    else:
                        xyz_DoA = self._Antenna.TxPos[self._Antenna.curr_tStep] - self.__Plane.RxPos
                        #calculate DoD
                        xyz_DoD = self.__Plane.RxPos-self._Antenna.TxPos[self._Antenna.curr_tStep]
                        self.H_vv = path_info[6 + offset_doppler].astype(complex) + 1j*path_info[7 + offset_doppler].astype(complex)
                        self.H_vh = path_info[8 + offset_doppler].astype(complex) + 1j*path_info[9 + offset_doppler].astype(complex)
                        self.H_hv = path_info[10 + offset_doppler].astype(complex) + 1j*path_info[11 + offset_doppler].astype(complex)
                        self.H_hh = path_info[12 + offset_doppler].astype(complex) + 1j*path_info[13 + offset_doppler].astype(complex)

                # Angles of arrival
                _, EoA, AoA = cart2sph(xyz_DoA[0], xyz_DoA[1], xyz_DoA[2])
                self.EoA = np.rad2deg(EoA)
                self.AoA = np.rad2deg(AoA)

                # Angles of departure
                _, EoD, AoD = cart2sph(xyz_DoD[0], xyz_DoD[1], xyz_DoD[2])
                self.EoD = np.rad2deg(EoD)
                self.AoD = np.rad2deg(AoD)
                    

def cart2sph(x, y, z):
    # Compute radius
    radius = np.sqrt(x**2 + y**2 + z**2)

    # Compute elevation (polar angle)
    elevation = np.arctan2(z, np.sqrt(x**2 + y**2))

    # Compute azimuth (azimuthal angle)
    azimuth = np.arctan2(y, x)

    return radius, elevation, azimuth

                    


                    
        

