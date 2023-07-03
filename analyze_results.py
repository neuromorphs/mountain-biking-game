#%%load data
from prefs import prefs
my_prefs=prefs()
from easygui import fileopenbox
import pandas as pd
f=fileopenbox('choose CSV file','CSV chooser', default='results/*.csv')
d=pd.read_csv(f,comment='#')

#%% plot error over time
import matplotlib.pyplot as plt
time=d['time(s)']
err=d['error']
plt.plot(time,err)
plt.show()
if 'trail_pos' in d.keys():
    trail_pos=d['trail_pos']
    plt.plot(time,trail_pos)

