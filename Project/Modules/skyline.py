# skyline module

import numpy as np
import matplotlib.pyplot as plt

# class to store the geometry of a rooftop on the skyline
class Roof:
    def __init__(self, tup=(-1, 1, -1)):
        self.phi1 = tup[0]
        self.phi2 = tup[1]
        self.theta = tup[2]
    
    def show(self):
        print "(phi1=" + str(self.phi1) + ", phi2=" + str(self.phi2) + ", theta=" + str(self.theta) +")"   



# class to store the geometry of the steps between consecutive rooftops on the skyline
class Cliff:
    def __init__(self, phi=None, theta_L=None, theta_R=None ):
        self.phi = phi
        self.theta_L = theta_L
        self.theta_R = theta_R
    
    def show(self):
        print "(phi=" + str(self.phi) + ", theta_L=" + str(self.theta_L) + ", theta_R=" + str(self.theta_R) +")"   
    


# class to store the skyline
class Silhouette:
    
    def __init__(self):
        self.cliffs = [] # list of cliffs ordered by phi
        # add the two extreme points
        self.cliffs.append(Cliff(-np.pi -1, 0,0))
        self.cliffs.append(Cliff(np.pi + 1, 0,0))
    
    def draw(self, ax, theta_offset, phi_offset, color='k', marker="None", fill=True, polar=False):
        gray_color = '#909090'
            
        if polar:
            phi_conversion_ratio = -1
            theta_conversion_ratio = 1

        else:
            phi_conversion_ratio = 180 / np.pi
            theta_conversion_ratio = 180 / np.pi
            theta_offset = 0
            phi_offset = 0   
        
        phi_list = []
        theta_list = []
        for cliff in self.cliffs:
            phi_list.append(cliff.phi * phi_conversion_ratio + phi_offset)
            theta_list.append(cliff.theta_L * theta_conversion_ratio + theta_offset)
            phi_list.append(cliff.phi * phi_conversion_ratio + phi_offset)
            theta_list.append(cliff.theta_R * theta_conversion_ratio + theta_offset)
         
        if polar:
            phi_list.pop(0)
            phi_list.pop(-1)
            phi_list.pop(0)
            phi_list.pop(-1)
            theta_list.pop(0)
            theta_list.pop(-1)
            theta_list.pop(0)
            theta_list.pop(-1)

            # coordinates = []
            # for i in range(0, len(phi_list)):
            #     coordinates.append( (phi_list[i], theta_list[i] ) )
            # coordinates.sort(key=lambda x: x[0])
            # phi_list = []
            # theta_list = []
            # for i in range(0, len(coordinates)):
            #     phi_list.append(coordinates[i][0])
            #     theta_list.append(coordinates[i][1])

            horizon_phi = np.array(phi_list)
            horizon_theta = horizon_phi*0 + theta_offset
            
            c1 = plt.polar(phi_list, theta_list, color=color)[0]
            c2 = plt.polar(horizon_phi, horizon_theta, color=color)[0]
            
            if fill:
                x1 = c1.get_xdata()
                y1 = c1.get_ydata()
                x2 = c2.get_xdata()
                y2 = c2.get_ydata()
                plt.fill_between(x1, y1, y2, color=color)
            
            dense_phi = np.arange(0, 2*np.pi, 0.01)
            horizon = dense_phi*0 + theta_offset
            c3 = plt.polar(horizon, color=gray_color)[0]
            x3 = c3.get_xdata()
            y3 = c3.get_ydata()
            plt.fill_between(dense_phi, 0, horizon, color=gray_color)
                

        else:
            if fill:
                ax.fill_between(phi_list, 0, theta_list, color=color, facecolor=color)
            else:
                ax.plot(phi_list, theta_list, color=color, marker=marker)

            # plot East, South and West markers as vertical lines
            ax.plot([-90, -90], [0, 90], color=gray_color)
            ax.plot([0, 0], [0, 90], color=gray_color)
            ax.plot([90, 90], [0, 90], color=gray_color)

            plt.text(-179, 1, 'N', color=gray_color)
            plt.text(-89, 1, 'E', color=gray_color)
            plt.text(1, 1, 'S', color=gray_color)
            plt.text(91, 1, 'W', color=gray_color)
            plt.text(175, 1, 'N', color=gray_color)
            
    def add_roof(self, roof):
        # find the cliffs that are between the roof's phi1 and phi2
        cliffs_inside = []
        insert_index_1 = 0
        insert_index_2 = 0

        i = 0
        while self.cliffs[i].phi < roof.phi1:
            insert_index_1 += 1
            insert_index_2 += 1
            i += 1
        while self.cliffs[i].phi < roof.phi2:
            insert_index_2 += 1
            i += 1
            
        # in case the entire roof falls between too cliffs
        if not self.cliffs[insert_index_1 : insert_index_2]:
            # get the silhouette's height from previous cliff
            theta = self.cliffs[insert_index_1 -1].theta_R
            # add only if it's higher
            if theta < roof.theta:
                cliff1 = Cliff(roof.phi1, theta, roof.theta)
                cliff2 = Cliff(roof.phi2, roof.theta, theta)
                self.cliffs.insert(insert_index_1, cliff1)
                insert_index_2 += 1 # the first insertion shift the index
                self.cliffs.insert(insert_index_2, cliff2)
                
        # in case the roof spans over at least one cliff
        else:
            
            # process the cliffs between the roof endpoints
            cliffs_to_delete = []
            for i in range(insert_index_1, insert_index_2):
                L = self.cliffs[i].theta_L
                R = self.cliffs[i].theta_R
                H = roof.theta
                
                # if the cliff is under the roof, delete it
                if L < H and R < H:
                    cliffs_to_delete.insert(0,i)
                
                # if the cliff crosses the roof downwards, update it
                elif L > H and R < H:
                    self.cliffs[i].theta_R = roof.theta
                
                # if the cliff crosses the roof upwards, update it
                elif L < H and R > H:
                    self.cliffs[i].theta_L = roof.theta
                
                # if the cliff is above the roof, it shouldn't change
            
            # process the endpoints of the roof
            theta1 = self.cliffs[insert_index_1 -1].theta_R
            theta2 = self.cliffs[insert_index_2].theta_L
            
            # add phi2 first
            if theta2 < roof.theta:
                cliff2 = Cliff(roof.phi2, roof.theta, theta2)
                self.cliffs.insert(insert_index_2, cliff2)
            
            # delete cliffs under the roof
            for index in cliffs_to_delete:
                self.cliffs.pop(index)
            
            # add phi1 last
            if theta1 < roof.theta:
                cliff1 = Cliff(roof.phi1, theta1, roof.theta)
                self.cliffs.insert(insert_index_1, cliff1)
 