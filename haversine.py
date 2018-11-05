import numpy as np

def hav(theta):
	return (np.sin(theta/2))**2

#returns distance in yards
def haversine_distance(start_lat,start_long,end_lat,end_long,R):
 	temp = np.deg2rad(np.sqrt(hav(end_lat-start_lat)+np.cos(start_lat)*np.cos(end_lat)*hav(end_long-start_long)))
 	temp = np.minimum(temp, 1)
 	temp = np.maximum(temp, -1)
 	return (5280/3)*2*R*np.arcsin(temp)