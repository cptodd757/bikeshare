import numpy as np
import pandas as pd
import matplotlib.pyplot as plt 
import time
import json
import urllib3
import certifi

use_cloud_credits = False


# 1. Data Visuals: Display or graph 3 metrics or trends from the data set that are interesting to you.
# 2. Which start/stop stations are most popular?
# 3. What is the average distance traveled?
# 4. How many riders include bike sharing as a regular part of their commute?
# (Optional) Bonus features you may want to include to stand out:

# How does ridership change with seasons? Types of passes used, trip duration, etc
# Is there a net change of bikes over the course of a day? If so, when and
# where should bikes be transported in order to make sure bikes match travel patterns?
# What is the breakdown of Trip Route Category-Passholder type combinations? What might make a particular combination more popular?


df = pd.read_csv('metro-bike-share-trip-data.csv',low_memory=False)

#2. Most popular start/stop stations
start_ids = df['Starting Station ID'].dropna().astype(np.int32)
end_ids = df['Ending Station ID'].dropna().astype(np.int32)
start_counts = start_ids.value_counts()
end_counts = end_ids.value_counts()
print(start_counts)

def remove_zeros(array):
	return [x for x in array if x != 0]


start_lats = remove_zeros(list(df['Starting Station Latitude'].dropna().values))
end_lats = remove_zeros(list(df['Ending Station Latitude'].dropna().values))
start_longs = remove_zeros(list(df['Starting Station Longitude'].dropna().values))
end_longs = remove_zeros(list(df['Ending Station Longitude'].dropna().values))
print('Minimum latitude: ',np.amin([np.amin(start_lats),np.amin(end_lats)]))
print('Maximum latitude: ',np.amax([np.amax(start_lats),np.amax(end_lats)]))
print('Minimum longitude: ',np.amin([np.amin(start_longs),np.amin(end_longs)]))
print('Maximum longitude: ',np.amax([np.amax(start_longs),np.amax(end_longs)]))


def hue_strength(color,strength):
	main_digits = hex(np.minimum(255, 383 - strength))[2:].zfill(2)
	other_digits = hex(np.maximum(0, 255 - strength))[2:].zfill(2)
	if color == 'blue':
		return "0x"+other_digits+other_digits+main_digits
	if color == 'red':
		return "0x"+main_digits+other_digits+other_digits
	if color == 'green':
		return "0x"+other_digits+main_digits+other_digits

#new df indexed by start id
id_df = df.set_index("Starting Station ID")
start_map_url = "https://maps.googleapis.com/maps/api/staticmap?size=640x640"
max_count = np.amax(list(start_counts.values))
print(len(start_counts.values))
for i in range(len(start_counts)):
	strength = int(255*start_counts.values[i]/max_count)
	color = hue_strength('green',strength)
	start_lat = id_df.loc[start_counts.index[i],"Starting Station Latitude"].iloc[0]
	start_long = id_df.loc[start_counts.index[i],"Starting Station Longitude"].iloc[0]
	if np.minimum(start_long,start_lat) == 0 or np.isnan(start_lat) or np.isnan(start_long):
		continue
	#manually get rid of two outliers, focus on heart of LA
	if start_long < -118.3:
		continue
	print(start_lat,start_long)
	char = chr(i+65)
	if i > 25:
		char = 'a'
	start_map_url += "&markers=color:" + color + "|size:mid|label:" + char + "|" + str(start_lat) + "," + str(start_long)
start_map_url += "&key=AIzaSyB4RyqCQ38yvJPqvC8lT8jJOqyJL52MrAA"
print(start_map_url)
start_map_url_file = open('start_map_url.txt','w')
start_map_url_file.write(start_map_url)

end_map_url = "https://maps.googleapis.com/maps/api/staticmap?size=640x640"
max_count = np.amax(list(end_counts.values))
for i in range(len(end_counts)):
	strength = int(255*end_counts.values[i]/max_count)
	color = hue_strength('red',strength)
	end_lat = id_df.loc[end_counts.index[i],"Ending Station Latitude"].iloc[0]
	end_long = id_df.loc[end_counts.index[i],"Ending Station Longitude"].iloc[0]
	if np.minimum(end_long,end_lat) == 0 or np.isnan(end_lat) or np.isnan(end_long):
		continue
	#manually get rid of two outliers, focus on heart of LA
	if end_long < -118.3:
	 	continue
	print(end_lat,end_long)
	char = chr(i+65)
	if i > 25:
		char = 'a'
	end_map_url += "&markers=color:" + color + "|size:mid|label:" + char + "|" + str(end_lat) + "," + str(end_long)
end_map_url += "&key=AIzaSyB4RyqCQ38yvJPqvC8lT8jJOqyJL52MrAA"
print(end_map_url)
end_map_url_file = open('end_map_url.txt','w')
end_map_url_file.write(end_map_url)



fig1, ax1 = plt.subplots()
ax1.bar(range(start_counts.size),list(start_counts.values),tick_label=list(start_counts.index))
fig2, ax2 = plt.subplots()
ax2.bar(range(end_counts.size),list(end_counts.values),tick_label=list(end_counts.index))
plt.show()







#3. Average distance traveled
def hav(theta):
	return (np.sin(theta/2))**2

#returns distance in yards
R = 3959
def haversine_distance(start_lat,start_long,end_lat,end_long):
 	temp = np.deg2rad(np.sqrt(hav(end_lat-start_lat)+np.cos(start_lat)*np.cos(end_lat)*hav(end_long-start_long)))
 	temp = np.minimum(temp, 1)
 	temp = np.maximum(temp, -1)
 	return (5280/3)*2*R*np.arcsin(temp)

df['haversine_distance'] = haversine_distance(df['Starting Station Latitude'],df['Starting Station Longitude'],df['Ending Station Latitude'],df['Ending Station Longitude'])	
#query = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins=40.6655101,-73.89188969999998&destinations=40.6905615,-73.9976592&mode=bicycling&key=AIzaSyB4RyqCQ38yvJPqvC8lT8jJOqyJL52MrAA"
	
sample = df.sample(n=100,random_state=900)
actual_dists = []
haversine_dists = []

file = open('distance_matrix_API_1000_sample.txt','a')
for i in range(len(sample)):
	#print(i)
	start_lat = sample.iloc[i]['Starting Station Latitude']
	start_long = sample.iloc[i]['Starting Station Longitude']
	end_lat = sample.iloc[i]['Ending Station Latitude']
	end_long = sample.iloc[i]['Ending Station Longitude']
	hdist = haversine_distance(start_lat,start_long,end_lat,end_long)
	if hdist == 0.0:
		continue
	
	if use_cloud_credits:
		http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
		headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
		query = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins="+str(start_lat)+","+str(start_long)+"&destinations="+str(end_lat)+","+str(end_long)+"&mode=bicycling&key=AIzaSyB4RyqCQ38yvJPqvC8lT8jJOqyJL52MrAA"
		req = http.request('GET', query, headers=headers)
		page = req.data.decode('utf-8')
		print(page)
		data = json.loads(page)
		
		if "distance" not in data["rows"][0]["elements"][0]:
			continue
		actual_dists.append(data["rows"][0]["elements"][0]["distance"]["value"])
		print(data["rows"][0]["elements"][0]["distance"]["text"])
		json.dump(data,file)
		file.write('\n')

	haversine_dists.append(hdist)

for dist in actual_dists:
	file.write(str(dist))
	file.write('\n')
hd_sample_mean = np.nanmean(haversine_dists)
ad_sample_mean = np.nanmean(actual_dists)
print(haversine_dists)
print(actual_dists)

hd_pop_mean = np.nanmean(remove_zeros(list(df['haversine_distance'].values)))

if use_cloud_credits:
	meanfile = open('google_distances_mean.txt','w')
	meanfile.write(ad_sample_mean)
else:
	meanfile = open('google_distances_mean.txt','r')
	ad_sample_mean = float(meanfile.read())

print(hd_pop_mean)
print(hd_sample_mean)
print(ad_sample_mean)

ratio = ad_sample_mean/hd_sample_mean

predicted_ad_pop_mean = ratio * hd_pop_mean
print(predicted_ad_pop_mean)

#4. Percentage of regular users
total = len(df)
regular = len(remove_zeros(list(df['Plan Duration'].dropna().values)))
print("Total users: ",total)
print("Regular users (non-walk-ups): ", regular)
print("Percentage of users who are regular: "+str(np.round(100*regular/total,2))+"%")