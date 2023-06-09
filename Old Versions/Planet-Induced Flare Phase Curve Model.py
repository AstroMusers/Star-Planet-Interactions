# -*- coding: utf-8 -*-
"""
Created on Sun May 14 18:28:00 2023

@author: Nate Whitsett
"""

import numpy as np
from matplotlib import pyplot as plt


##This defines the stellar parameters relevant in a magnetic star-planet induced flare.
##The parameters are mass (in solar masses), distance (in parsecs), luminosity
##(in log(L_{solar})), spectral class (O,B,A,F,G,K,M), and optional parameters are
##radius (solar radii), age (seconds, 1e9 -> 1 bly), rotational period (days),
##and surface magnetic field strength (Gauss)

##For the most part, all parameters are converted to CGS units if they are not
##already, except for luminosity, which is kept in Watts. This is because the
##interaction energy is quoted in Joules/Watts. It is converted later. 
##Typical terminal stellar windspeed is estimated to be approximately solar-like
##at 400 km/s.

##The mass-loss rate is assumed to be primarily a function of spectral type,
##with more massive, hotter stars undergoing more mass loss, and cooler, 
##less massive and convective stars, losing less. This is based on empirical
##trends from various sources.

##Most stellar magnetic fields are not known; thus, it is approximated by 
##stellar age, following an empirical power law of -1.32. Additionally,
##magnetic fields can be approximated by another empirical power law of
##power -0.655. 

##A crucial assumption of this code is that the stellar magnetic fields are
##approximately dipolar; consequently, the Alfven surface can be estimated
##using only the 'magnetic confinement parameter', eta. This is a function of
##surface stellar magnetic field strength, the star's radius, the terminal
##windspeed, and the mass loss rate. The Alfven surface is then determined by
##a 1/4 power law with respect to eta, which is scaled to the Sun's Alfven
##surface of 18.8 solar radii.
class Star:
    def __init__(self, mass, dist, lumin, spectral, radius=None, age=None, p_rot=None, B=None):
        self.mass = mass
        self.lumin = 10**(lumin)*3.8e26
        if radius == None:
            self.radius = (mass**0.8)*6.957e10
        elif radius != None:
            self.radius = radius*6.957e10
        self.age = age
        self.dist = dist*3.086e18
        self.p_rot = p_rot
        self.windspeed = 40000000
        self.spectral = spectral.lower()
        self.brightness = lumin/(4*np.pi*dist**2)
        if self.spectral == 'o':
            self.massloss = 1e-8
        if self.spectral == 'b':
            self.massloss = 1e-9
        if self.spectral == 'a':
            self.massloss = 1e-10
        if self.spectral == 'f':
            self.massloss = 1e-13
        if self.spectral == 'g':
            self.massloss = 1e-14
        if self.spectral == 'k':
            self.massloss = 1e-15
        if self.spectral == 'm':
            self.massloss = 1e-15
        if B != None:
            self.B = B
        if age == None and B == None:
            self.B = 10**1.98/(p_rot**(np.random.normal(1.32, 0.07)))
        if p_rot == None and B == None:
            self.B = 10**6.63/(age**(np.random.normal(0.655, 0.0225)))
        if p_rot == None and age == None and B == None:
            return 'Input age, rotational period, or B field'
        elif age != None and p_rot != None and B == None:
            self.B = (10**1.98/(0.25*p_rot**(np.random.normal(1.32, 0.07)))+ 0.75*10**6.63/(age**(np.random.normal(0.655, 0.0225))))
        self.eta = 0.4*((self.B/100)**2 * (self.radius/1e12)**2)/((self.windspeed/1e8)*(self.massloss/1e-6))
        self.Alfven = 0.0874*(0.3+(self.eta)**(1/4))
        
        
        
##This defines the planet. Since little is known about the parameters which
##dictate exoplanetary magnetic fields, this is manually inputted. The radius,
##eccentricity and semi-major axis, as well as the occultation phase, are the
##only other planetary parameters. Since this class keeps track of the orbital
##distance to the barycenter (assumed to be the host star), an 'orbital resolution'
##is defined which allows the user to simulate the instrument's phase
##sensitivity. 

##The radius is given in Jupiter radii, the semi-major axis in AU, and the
##magnetic field strength in Gauss. The phase related parameters are in radians.
class Planet:
    def __init__(self, radius, a, e, B, orbit_resolution=0.1, occ_phase = 0):
        self.radius = radius*7.149e9
        self.e = e
        self.a = a
        self.B = B
        self.phase = np.arange(0,2*np.pi, orbit_resolution)
        self.orbit = a*(1-e**2)/(1+e*np.cos(self.phase+occ_phase))
        self.orbit_resolution = orbit_resolution


##This interaction function takes as input a star and planet class, and will
##generate an array corresponding to a phase-dependent luminosity increase in 
##the host star. The luminosity increase follows the analysis by Antonio
##Lanza of weak-moderate stellar field strength. The energy is proportional
##to (B_{star}^2)(R_{star}^3) * (B_{planet}/B_{star})*(1/(star_planet distance/R_{star})^2)
##That is, the larger the star, the stronger the B field of the star, the
##stronger the B field of the planet to the star, and the closeness of approach
##of the planet all dictate the energy output. 

##The flare itself is given some energy based on the above relation. Then the
##total flare energy is released over some quasi-random timescale
##(corresponding to minutes-hours given a few day orbital period).

##The assumption is that the flare interaction cannot occur if the planet
##is not within its host's Alfven radius. The flare occurence can be modified
##by any scaling factor one wishes. As it stands, the probability is just a 
##linear increse towards some arbitrary probability as the orbit gets closer 
##to the star, though there is no real basis behind it other than intuition.
##The probability is normalized to each step, so increasing the step size
##will not increase the total probability of a flare.
def interaction(star, planet):
    probability = 0
    brightness_increase = []
    flare = False
    counter = 0
    phase_blocks = 0
    flare_count = 0
    flare_strength = 0
    for orbit in planet.orbit:
        threshold = np.random.random()
        if orbit > star.Alfven and flare == False:
            probability = 0
            brightness_increase.append(0)
        if orbit <= star.Alfven and flare == False:
            probability = (star.Alfven - orbit)/(star.Alfven)*0.5*(1/len(planet.orbit))
            if probability > threshold:
                flare = True
                flare_count += 1
                counter = 0
                total_energy = 1e-7*(star.B**2*(star.radius)**3)*((((planet.B/star.B)*0.04)/((orbit*1.496e13)/star.radius)**2))
                flare_time = 0.03 - 0.015*np.random.random()
                phase_blocks = int(len(planet.orbit)*flare_time)
            elif probability <= threshold:
                brightness_increase.append(0)
        if flare == True and counter <= phase_blocks:
            brightness_increase.append((total_energy/phase_blocks*(np.random.normal(1, 0.02)))/star.lumin)
            counter += 1
        if counter == phase_blocks:
            flare_strength = ((((planet.B/star.B)*0.04)/((orbit*1.496e13)/star.radius)**2))
            flare = False
            counter = 0
    return brightness_increase, flare_count, flare_strength


def phase_curve(star, planet, interaction, transit_displacement=np.pi):
    base = []
    subtraction = []
    transit_displacement = int((transit_displacement/(2*np.pi))*len(planet.orbit))
    ingress_phase = int(np.arccos(1-(planet.radius*2)**2/(2*(planet.orbit[transit_displacement]*1.496e13)**2))/(2*np.pi)*len(planet.orbit))
    transit_phase = int(np.arccos(1-(star.radius*2)**2/(2*(planet.orbit[transit_displacement]*1.496e13)**2))/(2*np.pi)*len(planet.orbit))
    for steps in range(len(planet.phase)):
        base.append(star.brightness*(np.random.normal(1, 0.0001)))
    for phases in range(len(planet.orbit)):
        if phases < transit_displacement:
            subtraction.append(0)
        elif phases >= transit_displacement and phases < (transit_displacement + ingress_phase):
            subtraction.append((-((phases-transit_displacement)/ingress_phase)*(planet.radius**2/star.radius**2))*star.brightness)
        elif phases < (ingress_phase + transit_displacement) + transit_phase:
            subtraction.append(-(planet.radius**2/star.radius**2)*star.brightness)
        elif phases == (ingress_phase + transit_displacement) + transit_phase and phases <= (2*ingress_phase + transit_displacement) + transit_phase:
            subtraction.append(-((((ingress_phase + transit_displacement) + transit_phase)-phases)*(planet.radius**2/star.radius**2))*star.brightness)
        elif phases > (2*ingress_phase + transit_displacement) + transit_phase:
            subtraction.append(0)
    while len(subtraction) < len(base):
        subtraction.append(0)
    base= np.array(base)
    subtraction = np.array(subtraction)
    interaction = np.array(interaction)
    curve = np.add(base,subtraction)
    return np.add(interaction,curve)

        
star = Star(2, 1, 1, 'm', radius=1, B=1)        
planet = Planet(1, 0.2, .9, 100, orbit_resolution=0.001, occ_phase = np.pi)
a, b,c = interaction(star, planet)
print(b,c)
plt.plot(planet.phase, phase_curve(star, planet, a))     
plt.xlim(0,2*np.pi)
print(((((planet.B/star.B)*0.04)/((min(planet.orbit)*1.496e13)/star.radius)**2)))
# theta = np.arange(0, 2*np.pi, 0.01)
# fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
# ax.plot(planet.phase, planet.orbit)
# ax.plot(theta, np.full(shape=len(theta), fill_value=star.Alfven))
# ax.set_rmax(2)
# ax.grid(True)
