import numpy as np
import pandas as pd
import matplotlib.pyplot as plt 
import time
import json
import urllib3
import certifi
from heatmap import heatmap
from haversine import haversine_distance

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

df = pd.read_csv('data/metro-bike-share-trip-data.csv',low_memory=False)

def get_month(x):
	return x[5:7]
def get_year(x):
	return x[2:4]
def months_since_start(x):
	return int(x[5:7]) - 7 + 12*(int(x[2:4]) - 16)
def get_specific_month(x):
	months = ["July '16","August '16","September '16","October '16","November '16","December '16",
			"January '17","February '17","March '17"]
	return months[x]
def numeric_time(x):
	return int(pd.Timestamp(x).to_pydatetime().timestamp())
def get_hour(x):
	return x[-8:-6]
df['Month'] = df['Start Time'].apply(get_month)
df['Year'] = df['Start Time'].apply(get_year)
df['Time Elapsed'] = df['Start Time'].apply(months_since_start)
df['Month-Year'] = df['Time Elapsed'].apply(get_specific_month)
df['Numeric Time'] = df['Start Time'].apply(numeric_time)
df['Hour'] = df['Start Time'].apply(get_hour)

def remove_zeros(array):
	return [x for x in array if x != 0]
def convert_to_months(indices, values):
	months = ["July '16","August '16","September '16","October '16","November '16","December '16",
			"January '17","February '17","March '17"]
	indices = list(indices)
	values = list(values)
	for i in range(len(months)):
		if i not in indices:
			indices.insert(i, i)
			values.insert(i, 0)
	return [months[x] for x in indices], values

#1. 3 interesting trends:
#a. average duration of trip vs. months for each bike
df_grouped = df.groupby(['Bike ID','Time Elapsed'])['Duration'].mean() 
bike_ids = [int(x) for x in list(df_grouped.index.levels[0])]

fig, ax = plt.subplots(figsize=(12,6))
fig_name = 'data/line-graphs/bike-ids'
count = 0
for i in range(len(bike_ids)):
	bike_data = df_grouped[bike_ids[i]]
	if len(bike_data.values) > 3 and bike_data.values[-1] < bike_data.values[-2] and bike_data.values[-2] < bike_data.values[-3] and bike_data.values[-3] < bike_data.values[-4]:
		indices, values = convert_to_months(bike_data.index, bike_data.values)
		ax.plot(indices, values, label=bike_ids[i])
		ax.legend(title="Bike IDs")
		fig_name = fig_name + '-' + str(bike_ids[i])
		if (count+1)%5 == 0:
			ax.set_xlabel("Month")
			ax.set_ylabel("Average duration (sec) per month")
			ax.set_title("Average Duration of Rides Each Month")
			fig_name += '.png'
			fig.savefig(fig_name)
			fig, ax = plt.subplots(figsize=(12,6))
			fig_name = 'data/line-graphs/bike-ids'
		count += 1

#b. Where are walkups most frequent
walkup_counts = df.groupby(['Passholder Type']).get_group('Walk-up')['Starting Station ID'].dropna().astype(np.int32).value_counts()
heatmap(df,walkup_counts,'data/heatmaps/walkup_start_heatmap_url','blue','Starting')

#c. popularity of each station versus month: 8 * 2 total heatmaps
df_grouped = df.groupby(['Time Elapsed'])
months = ["July '16","August '16","September '16","October '16","November '16","December '16",
			"January '17","February '17","March '17"]
m = 0
for time, group in df_grouped:
	start_ids_grouped = df_grouped.get_group(time).groupby(['Starting Station ID'])
	month = months[m]
	heatmap(df, group['Starting Station ID'].value_counts(), 'data/heatmaps/months/start/' + month[0:3] + month[-2:] + 'start_heatmap_url','blue','Starting')
	heatmap(df, group['Ending Station ID'].value_counts(), 'data/heatmaps/months/end/' + month[0:3] + month[-2:] + 'end_heatmap_url','blue','Ending')
	m += 1



#2. Most popular start/stop stations
start_ids = df['Starting Station ID'].dropna().astype(np.int32)
end_ids = df['Ending Station ID'].dropna().astype(np.int32)
start_counts = start_ids.value_counts()
end_counts = end_ids.value_counts()
heatmap(df,start_counts,'data/heatmaps/start_heatmap_url','green','Starting')
heatmap(df,end_counts,'data/heatmaps/end_heatmap_url','red','Ending')

#3. Average distance traveled
df['haversine_distance'] = haversine_distance(df['Starting Station Latitude'],df['Starting Station Longitude'],df['Ending Station Latitude'],df['Ending Station Longitude'],3959)	
	
sample = df.sample(n=100,random_state=900)
actual_dists = []
haversine_dists = []

file = open('data/distance_matrix_API_100_sample.txt','a')
for i in range(len(sample)):
	start_lat = sample.iloc[i]['Starting Station Latitude']
	start_long = sample.iloc[i]['Starting Station Longitude']
	end_lat = sample.iloc[i]['Ending Station Latitude']
	end_long = sample.iloc[i]['Ending Station Longitude']
	hdist = haversine_distance(start_lat,start_long,end_lat,end_long,3959)
	if hdist == 0.0:
		continue
	
	if use_cloud_credits:
		http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())
		headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
		query = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins="+str(start_lat)+","+str(start_long)+"&destinations="+str(end_lat)+","+str(end_long)+"&mode=bicycling&key=AIzaSyB4RyqCQ38yvJPqvC8lT8jJOqyJL52MrAA"
		req = http.request('GET', query, headers=headers)
		page = req.data.decode('utf-8')
		data = json.loads(page)
		if "distance" not in data["rows"][0]["elements"][0]:
			continue
		actual_dists.append(data["rows"][0]["elements"][0]["distance"]["value"])
		json.dump(data,file)
		file.write('\n')
	haversine_dists.append(hdist)

for dist in actual_dists:
	file.write(str(dist))
	file.write('\n')
hd_sample_mean = np.nanmean(haversine_dists)
ad_sample_mean = np.nanmean(actual_dists)
hd_pop_mean = np.nanmean(remove_zeros(list(df['haversine_distance'].values)))

if use_cloud_credits:
	meanfile = open('data/google_distances_mean.txt','w')
	meanfile.write("sample mean: " + str(ad_sample_mean))
	meanfile.close()
else:
	meanfile = open('data/google_distances_mean.txt','r')
	meanfile.readline()
	ad_sample_mean = float(meanfile.readline())
	meanfile.close()

meanfile = open('data/google_distances_mean.txt','w')
ratio = ad_sample_mean/hd_sample_mean
predicted_ad_pop_mean = ratio * hd_pop_mean
meanfile.write("Actual distance sample mean: \n" + str(ad_sample_mean))
meanfile.write("\nPredicted actual distance population mean: \n" + str(predicted_ad_pop_mean))

#4. Percentage of regular users
file = open('data/percentage-regular-users.txt','w')
total = len(df)
regular = len(remove_zeros(list(df['Plan Duration'].dropna().values)))
file.write("Total users: " + str(total) + '\n')
file.write("Regular users (non-walk-ups): " + str(regular) + '\n')
file.write("Percentage of users who are regular: "+str(np.round(100*regular/total,2))+"%")

#Bonus:
#a. change over seasons: duration vs. time and freq vs. time, each type of pass gets its own line
df_grouped = df.groupby(['Passholder Type'])

#duration vs. month
fig1, ax1 = plt.subplots(figsize=(12,6))

#frequency vs. month 
fig2, ax2 = plt.subplots(figsize=(12,6))

for pass_type, group in df_grouped:
	by_months = group.groupby(['Time Elapsed'])
	means = by_months['Duration'].mean()
	indices, values = convert_to_months(means.index, means.values)
	ax1.plot(indices, values, label=pass_type)

	counts = group['Time Elapsed'].value_counts().sort_index()
	indices, values = convert_to_months(counts.index, counts.values)
	ax2.plot(indices, values, label=pass_type)

ax1.set_xlabel("Month")
ax1.set_ylabel("Average duration of rides (seconds)")
ax1.set_title("Duration of Rides vs. Time of Year")
ax1.legend(title="Pass Type")
fig1.savefig('data/line-graphs/duration-vs-month.png')

ax2.set_xlabel("Month")
ax2.set_ylabel("Number of rides")
ax2.set_title("Number of Rides vs. Time of Year")
ax2.legend(title="Pass Type")
fig2.savefig('data/line-graphs/frequency-vs-month.png')

#b. popularity vs. time of day for each station
df_grouped = df.groupby(['Hour'])
for time, group in df_grouped:
	start_ids_grouped = df_grouped.get_group(time).groupby(['Starting Station ID'])
	heatmap(df, group['Starting Station ID'].value_counts(), 'data/heatmaps/hours/start/hour' + group['Hour'].iloc[0] + 'start_heatmap_url','blue','Starting')
	heatmap(df, group['Ending Station ID'].value_counts(), 'data/heatmaps/hours/end/hour' + group['Hour'].iloc[0] + 'end_heatmap_url','blue','Ending')

df_grouped = df.groupby(['Passholder Type'])
fig, ax = plt.subplots(figsize=(12,6))
for pass_type, group in df_grouped:
	counts = group['Hour'].value_counts().sort_index()
	ax.plot(counts.index, counts.values, label=pass_type)

ax.set_xlabel("Time of Day (hour)")
ax.set_ylabel("Number of Rides")
ax.legend()
ax.set_title("Number of Rides vs. Time of Day")
fig.savefig('data/line-graphs/frequency-vs-hour.png')

#c. Breakdown of Trip Route Category vs. Passholder Type
file = open('data/route-cat-vs-pass-type.txt','w')
df_grouped = df.groupby(['Passholder Type'])
for name, group in df_grouped:
	print(group['Trip Route Category'].value_counts()[0])
	percent = group['Trip Route Category'].value_counts()[0]/len(group)
	file.write(str(name) + ": " + str(percent*100) + '% were One-Way\n')#, group.value_counts())


plt.show()