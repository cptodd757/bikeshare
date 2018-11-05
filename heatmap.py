import numpy as np
import pandas as pd
import matplotlib.pyplot as plt 
import time
import json
import urllib3
import certifi


def heatmap(df, counts, filename, base_color, startOrEnd):
	id_df = df.set_index(startOrEnd + " Station ID")
	map_url = "https://maps.googleapis.com/maps/api/staticmap?size=640x640"
	max_count = np.amax(list(counts.values))
	map_legend = {}
	for i in range(len(counts)):
		strength = int(255*counts.values[i]/max_count)
		color = hue_strength(base_color,strength)
		lat = id_df.loc[counts.index[i],startOrEnd + " Station Latitude"].iloc[0]
		longg = id_df.loc[counts.index[i],startOrEnd + " Station Longitude"].iloc[0]
		if np.minimum(longg,lat) == 0 or np.isnan(lat) or np.isnan(longg):
			continue
		#manually get rid of two outliers, focus on heart of LA
		if longg < -118.3:
			continue
		#print(lat,longg)
		char = chr(i+65)
		if i > 25:
			char = 'a'
		else:
			map_legend[char] = []
			map_legend[char].append(str(counts.index[i]))
			map_legend[char].append(str(counts.values[i]))
		map_url += "&markers=color:" + color + "|size:mid|label:" + char + "|" + str(lat) + "," + str(longg)
	map_url += "&key=AIzaSyB4RyqCQ38yvJPqvC8lT8jJOqyJL52MrAA"
	#print(start_map_url)
	map_url_file = open(filename + '.txt','w')
	map_url_file.write(map_url)

	table_file = open(filename + '_table.json','w')
	#print(map_legend)
	json.dump(map_legend,table_file)



def hue_strength(color,strength):
	main_digits = hex(np.minimum(255, 383 - strength))[2:].zfill(2)
	other_digits = hex(np.maximum(0, 255 - strength))[2:].zfill(2)
	if color == 'blue':
		return "0x"+other_digits+other_digits+main_digits
	if color == 'red':
		return "0x"+main_digits+other_digits+other_digits
	if color == 'green':
		return "0x"+other_digits+main_digits+other_digits