#!/var/www/fgo-solomon-stats/.venv/bin/python

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import gspread
import matplotlib.dates as mdates
import matplotlib
from imgurpython import ImgurClient
from oauth2client.service_account import ServiceAccountCredentials
import subprocess
from datetime import datetime
import os
import shutil

print("{}: Starting ...".format(datetime.now()))
base_path = "/var/www/fgo-solomon-stats/"
base_img_path = base_path + "output/"

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name(base_path + 'google-api.json', scope)

gc = gspread.authorize(credentials)
rows = gc.open_by_key('1V8BhdZ0mT0IA0rX6xf_YNE31L3vo2W5moaM1MTNcuyQ').sheet1.get_all_values()
df = pd.DataFrame.from_records(rows)

df.columns = df.iloc[0] #First row as header
df = df.reindex(df.index.drop(0))
for col in ['percent', 'hp', 'time captured', 'time parsed']:
    df[col]= pd.to_numeric(df[col])

bosses = [boss for boss in list(df["id"].unique()) if not pd.isnull(boss) and boss != '']
boss_df = {}
for boss in bosses:
    boss_df[boss] = df[df["id"] == boss].sort_values("time captured")
print("{}: Downloaded and imported data".format(datetime.now()))

#Need to improve this part: Make the HP list increasing only
for i in range(10):
    for boss in boss_df:
        boss_df[boss] = boss_df[boss][boss_df[boss]["hp"] > boss_df[boss]["hp"].shift(1).fillna(0)] #Increasing HP only

boss_color = {
    'flauros': '#d62728',
    'forneus': '#9467bd',
    'barbatos': '#1f77b4',
    'halphas': '#ff7f0e',
    'amon_ra': '#bcbd22',
    'sabnock': '#7f7f7f',
    'andromalius': '#e377c2'
}
boss_name = {
    'flauros':'Flauros',
    'forneus': 'Forneus',
    'barbatos': 'Barbatos',
    'halphas': 'Halphas',
    'amon_ra': 'Amon Ra',
    'sabnock': 'Sabnock',
    'andromalius': 'Andromalius'
}
boss_interval = {
    'flauros': 4,
    'forneus': 4,
    'barbatos': 1,
    'halphas': 8,
    'amon_ra': 8,
    'sabnock': 4,
    'andromalius': 3,
    'all_kps': 8,
    'all_kps_except_barbatos': 8,
    'all_kills_counts': 8
}

h_fmt = mdates.DateFormatter('%m-%d %H')
start_time = pd.to_datetime("2018-12-20 23:00")

def hour_to_max(timestamp, interval):
    to_max = interval - ((timestamp.hour + 1) % interval) #+1 because start at 23:00
    return np.datetime64(timestamp, 'h') + np.timedelta64(to_max, 'h')

for boss in boss_df:
    x = boss_df[boss]["time captured"][1:]
    y = (boss_df[boss]["hp"].diff()[1:] / boss_df[boss]["time captured"].diff()[1:])
    if boss == 'barbatos':
        idx = (y < 500) & (y > 0) #Some bound checking
    else:
        idx = (y < 30) & (y > 0)
    x = x[idx][9:]
    x = pd.to_datetime(x, unit='s') + pd.Timedelta('-08:00:00') #Change time to PST time
    y = y[idx]
    y = y.rolling(10).mean()[9:] #Rolling average to smooth out

    z = boss_df[boss]["hp"][1:][idx][9:]

    data = {"time": x, "hp": z, "kps": y}
    df = pd.DataFrame.from_dict(data)
    df.to_csv(base_img_path + boss + ".csv", index = False)

    plt.style.use('seaborn')
    fig, ax = plt.subplots(figsize=(14, 7.5))
    ax.plot(x, y, color=boss_color[boss])
    
    if boss == 'andromalius':
        plt.ylim(bottom=0)
    else:
        hour_interval = boss_interval[boss]
        hours = mdates.HourLocator(interval = hour_interval)
        ax.xaxis.set_major_locator(hours)
        max_time = hour_to_max(x.iloc[-1], hour_interval)
        ax.set_xlim(start_time, max_time)
    
    ax.xaxis.set_major_formatter(h_fmt)
    fig.autofmt_xdate()
    plt.title("{} - updated {} PST".format(boss_name[boss], str(x.iloc[-1])))
    plt.xlabel("Pacific Standard Time (Month-Date Hour)")
    plt.ylabel("Kills per second")
    plt.savefig(base_img_path + str(boss) + ".png", dpi=200, bbox_inches='tight')
print("{}: Finished plotting individual pillars".format(datetime.now()))

def all_kps_plot(boss_dict, output_name, title):
    plt.style.use('seaborn')
    fig, ax = plt.subplots(figsize=(14, 7.5))
    hour_interval = boss_interval[output_name]
    hours = mdates.HourLocator(interval = hour_interval)
    ax.xaxis.set_major_locator(hours)
    ax.xaxis.set_major_formatter(h_fmt)
    update_time = pd.to_datetime("2018-12-01")
    
    for boss in boss_dict:
        x = boss_df[boss]["time captured"][1:]
        y = (boss_df[boss]["hp"].diff()[1:] / boss_df[boss]["time captured"].diff()[1:])
        if boss == 'barbatos':
            idx = (y < 500) & (y > 0) #Some bound checking
        else:
            idx = (y < 30) & (y > 0)
        x = x[idx]
        x = pd.to_datetime(x, unit='s') + pd.Timedelta('-08:00:00') #Change time to PST time
        if x.iloc[-1] > update_time:
            update_time = x.iloc[-1]
        y = y[idx]
        y = y.rolling(10).mean() #Rolling average to smooth out
        ax.plot(x, y, label=boss_name[boss], color=boss_color[boss])

    print("{}: Update time: {}".format(datetime.now(), update_time))
    plt.title("{} - updated {} PST".format(title, str(update_time)))
    plt.xlabel("Pacific Standard Time (Month-Date Hour)")
    plt.ylabel("Kills per second")
    max_time = hour_to_max(update_time, hour_interval)
    ax.set_xlim(start_time, max_time)
    fig.autofmt_xdate()
    plt.legend()
    plt.savefig(base_img_path + output_name + ".png", dpi=200, bbox_inches='tight')

all_kps_plot(boss_df, "all_kps", "All KPS")

all_kps_plot([boss for boss in boss_df if boss != "barbatos"], "all_kps_except_barbatos", "All KPS except Barbatos")

#all_kps_plot([boss for boss in boss_df if boss in ['forneus', 'halphas','amon_ra']], "non_fixed_bosses.png", "Non-fixed bosses")
print("{}: Finished plotting all pillars".format(datetime.now()))

def all_hp_plot(boss_dict, output_name, title):
    plt.style.use('seaborn')
    fig, ax = plt.subplots(figsize=(14, 7.5))
    hour_interval = boss_interval[output_name]
    hours = mdates.HourLocator(interval = hour_interval)
    ax.xaxis.set_major_locator(hours)
    ax.xaxis.set_major_formatter(h_fmt)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    update_time = pd.to_datetime("2018-12-01")

    for boss in boss_dict:
        x = boss_df[boss]["time captured"]
        y = boss_df[boss]["hp"]
        x = pd.to_datetime(x, unit='s') + pd.Timedelta('-08:00:00') #Change time to PST time
        if x.iloc[-1] > update_time:
            update_time = x.iloc[-1]
        ax.plot(x, y, label=boss_name[boss], color=boss_color[boss])

    plt.title("{} - updated {} PST".format(title, str(update_time)))
    plt.xlabel("Pacific Standard Time (Month-Date Hour)")
    plt.ylabel("Kills count")
    max_time = hour_to_max(update_time, hour_interval)
    ax.set_xlim(start_time, max_time)
    fig.autofmt_xdate()
    plt.legend()
    plt.savefig(base_img_path + output_name + ".png", dpi=200, bbox_inches='tight')

all_hp_plot(boss_df, "all_kills_counts", "All Kills Counts")
print("{}: Finished plotting all HPs".format(datetime.now()))

file_list = [
    'all_kps.png',
    'all_kps_except_barbatos.png',
    'all_kills_counts.png',
    'barbatos.png',
    'forneus.png',
    'flauros.png',
    'sabnock.png',
    'halphas.png',
    'andromalius.png',
    'amon_ra.png'
]
file_list = [base_img_path + file for file in file_list]

for file in file_list:
    with open(os.devnull, "w") as f:
        subprocess.call(["ect", file], stdout=f)
    shutil.copy2(file, "/var/www/fgo.square.ovh/solomon-raid-stats/")
    print("{}: Copied {}".format(datetime.now(), file))

print("{}: Script finished".format(datetime.now()))

