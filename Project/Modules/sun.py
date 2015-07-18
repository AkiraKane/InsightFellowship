# sun modul

import numpy as np
import datetime as dt
from dateutil.parser import parse

class SunPath:
    
    def __init__(self, lat=None, lon=None, date=dt.datetime.today().date()):
        self.positions = []  # list of tuples (phi, theta)
        self.visible = []
        self.lat = lat
        self.lon = lon
        self.date = date

    def get_date(self, date_str):
        # extract month and day from string such as "4/13"
        try:
            self.date = parse(date_str)
        except:
            print "Warning: input date cannot be parsed, using default: today()"


    def get_sun_vector(self):
        # convert to datetime
        start_date = dt.datetime(2000,1,1)

        # the number of days from 1 Jan 2000
        n = (self.date - start_date).days

        # mean longitude of the Sun
        L_deg = (280.460 + 0.9856474 * n) % 360

        # mean anomaly of the Sun
        g_deg = (357.528 + 0.9856003 * n) % 360
        g_rad = g_deg * np.pi/180

        # ecliptic longitude
        lambda_deg = L_deg + 1.915 * np.sin(g_rad) + 0.020 * np.sin(2*g_rad)
        lambda_rad = lambda_deg * np.pi/180

        # obliquity of the ecliptic
        eps_deg = 23.439 - 0.0000004 * n
        eps_rad = eps_deg * np.pi/180

        # Sun's unit vector (in equatorial coordinates) for this day
        u_sun = np.array([
                    np.cos(lambda_rad), \
                    np.cos(eps_rad) * np.sin(lambda_rad), \
                    np.sin(eps_rad) * np.sin(lambda_rad)\
                ])
        return u_sun

    # cities GPS coordinates
    def get_city_vectors(self, greenwich_time_minutes):

        minute2deg = 360.0/1440.0

        theta_city_deg = 90 - self.lat
        theta_city_rad = theta_city_deg * np.pi/180

        phi_city_deg = greenwich_time_minutes * minute2deg + self.lon
        phi_city_rad = phi_city_deg * np.pi/180

        # city's unit vector
        u_r = np.array([
                    np.sin(theta_city_rad) * np.cos(phi_city_rad),
                    np.sin(theta_city_rad) * np.sin(phi_city_rad),
                    np.cos(theta_city_rad)
                ])
        u_theta = np.array([
                    np.cos(theta_city_rad) * np.cos(phi_city_rad),
                    np.cos(theta_city_rad) * np.sin(phi_city_rad),
                    -np.sin(theta_city_rad)
                ])
        u_phi = np.array([
                    -np.sin(phi_city_rad),
                    np.cos(phi_city_rad),
                    0
                ])
        return (u_r, u_theta, u_phi)


    def calculate_path(self):
            
        u_sun = self.get_sun_vector()

        for time_minutes in range(0, 1440):
            (u_r, u_theta, u_phi) = \
                self.get_city_vectors(time_minutes)

            # calculate height of the Sun on the sky
            theta_rad = np.pi/2 - np.arccos( np.dot(u_r, u_sun) )
            
            if theta_rad > 0:
                # calculate projected Sun vector
                u_sun_projected = u_sun - u_r * np.dot(u_r, u_sun)
                u_sun_projected = u_sun_projected / \
                    np.sqrt(np.dot(u_sun_projected, u_sun_projected))

                # calculate azimuth of Sun
                phi_rad = np.arccos( np.dot(u_sun_projected, u_theta) )
                if np.dot(u_sun_projected, u_phi) > 0:
                    phi_rad *= -1

                self.positions.append( (phi_rad, theta_rad) )
            
            self.positions.sort(key=lambda t:t[0])

    def calculate_visibility(self, sil):
        cliff_index = 0
        for p in self.positions:
            while sil.cliffs[cliff_index].phi < p[0]:
                cliff_index += 1
            vis = sil.cliffs[cliff_index].theta_L < p[1]
            self.visible.append( vis )
        return (sum(self.visible), len(self.positions))
        
    def draw(self, ax, color='r', deg=True):
        if deg:
            phis = []
            thetas = []
            for p in self.positions:
                phis.append(p[0] * 180/np.pi)
                thetas.append(p[1] * 180/np.pi)
            ax.plot(phis, thetas, color=color)
        else:
            ax.plot(self.phi_list, self.theta_list, color=color)
      