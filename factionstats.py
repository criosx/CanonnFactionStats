import os.path
import pandas as pd
import pickle
import time
import plotly.plotly as py
import plotly.graph_objs as go
import plotly
import io
import requests



class FactionStats:
    def __init__(self):
        # load list with stat data from file
        # structure of list is [[time, systems pandas dataframe, factions pandas dataframe]]

        if os.path.isfile('./statdata/factionstat.dat'):
            self.factionstat = self.fn_load_object('./statdata/factionstat.dat')
        else:
            self.factionstat = []

    def fn_get_system_snapshots(self, systems, factions):
        # Creates a dictionary of systems containing pandas dataframe snapshots
        # Format of the data frame:
        # Faction Influence FactionState LastTimeUpdated
        # ...     ...       ...           ...
        # ...     ...       ...           ...

        snapshot = {}

        for system in systems.index:
            data = pd.DataFrame(columns=['Faction', 'Influence', 'Faction State', 'Last Time Updated'])
            factions_present = systems.loc[system, 'minor_faction_presences']
            for faction in factions_present:
                influence = faction['influence']
                state = faction['state']
                updated = systems.loc[system, 'updated_at']
                factionname = factions.loc[faction['minor_faction_id'], 'name']
                data.loc[data.shape[0]] = [factionname, influence, state, updated]
            snapshot[system] = data.copy()

        return snapshot

    def fn_load_object(self, filename):

        fi = open(filename, "r")
        po = pickle.load(fi)
        fi.close()

        return po

    def fn_plot_system_history(self, webpublishing=False):
        # Plots the influence history of a given system saves data and plots
        # Format:
        # Time Faction1 Faction2 ...
        # ...  ...      ...      ...
        # ...  ...      ...      ...

        # Create a list of snapshots over the last 90 days

        py.sign_in('criosix','3jLviaVFikQOH1BZRcew')
        published_plots=[]

        history=[]
        for entry in self.factionstat:
            if (time.time()-time.mktime(time.strptime(entry[0]))) < (90*24*60*60+1):
                history.append(self.fn_get_system_snapshots(entry[1], entry[2]))

        # Get a list of all occupied systems

        systemlist=[]
        for entry in history:
            for system in entry:
                if system not in systemlist:
                    systemlist.append(system)

        #Create data and plots for all systems
        for system in systemlist:

            # Get list of all factions
            factionlist=[]
            for entry in history:
                for faction in entry[system]['Faction'].tolist():
                    if faction not in factionlist:
                        factionlist.append(faction)

            # Create Data
            factionlist.sort()
            headerline = ['Date']+factionlist
            data = pd.DataFrame(columns=headerline)

            for entry in history:
                nextline = []
                for faction in factionlist:
                    if faction in entry[system]['Faction'].tolist():
                        i = entry[system]['Faction'].tolist().index(faction)
                        nextline.append(entry[system]['Influence'].tolist()[i])
                        date = entry[system]['Last Time Updated'].tolist()[0]
                    else:
                        nextline.append(0.0)

                data.loc[data.shape[0]] = [date]+nextline

            data.to_csv('./plotdata/' + system + '_history.dat', index=False)

            # Create Plots with Plotly
            # snapshots

            # Create current snapshots and save the data for future plotting

            snapshot = history[-1].copy()
            snapshot[system].sort_index()
            snapshot[system].to_csv('./plotdata/'+system+'_snapshot.dat', index=False)

            # Use matplotlib to create plots
            # Snapshots
            labels = snapshot[system]['Faction'].tolist()
            for i, val in enumerate(labels):
                if snapshot[system]['Faction State'].tolist()[i] != 'None':
                    labels[i] = val + ' (' + snapshot[system]['Faction State'].tolist()[i] + ')'
            values = snapshot[system]['Influence'].tolist()
            centertext = str(snapshot[system]['Last Time Updated'].tolist()[0]).split()[0]+'<br>'+\
                         str(snapshot[system]['Last Time Updated'].tolist()[0]).split()[1]
            layout = {'annotations': [{"font": {'color': 'rgb(207,217,220)'}, "showarrow": False, "text": centertext}],
                      'paper_bgcolor': 'rgb(55,71,79)', 'plot_bgcolor': 'rgb(55,71,79)', 'font': {'color': 'rgb(207,217,220)'},
                      'legend': {'orientation': 'h'}, 'autosize': True, 'height': 700}

            pietrace = go.Pie(labels=labels, values=values, hoverinfo="label+percent", hole=.4)

            plotlyfig = go.Figure(data=[pietrace], layout=layout)

            #py.image.save_as(plotlyfig, filename='./plots/' + system + '_snapshot.png')

            if webpublishing:
                trycounter = 1
                while trycounter < 6:
                    try:
                        print ('Attempting to publish '+system + '_snapshot, attempt #'+str(trycounter))
                        url_name = py.plot(plotlyfig,filename=system + '_snapshot', auto_open=False)
                        published_plots.append(url_name)
                        trycounter = 6
                    except:
                        print ('Failed to publish '+system+'_history')
                        print ('Waiting for 30 s ...')
                        print time.sleep(30)
                        trycounter += 1

            # History
            traces = []
            for faction in factionlist:
                trace = go.Scatter(x=data['Date'].tolist(), y=data[faction].tolist(), mode='lines+markers'
                                   , name=faction, line=dict(shape='spline'))
                traces.append(trace)

            layout = {'xaxis': {'title': 'Date', 'mirror': True, 'showline': True, 'color': 'rgb(207,217,220)'},
                      'yaxis': {'title': 'Influence (%)', 'mirror': True, 'showline': True, 'color': 'rgb(207,217,220)'},
                      'paper_bgcolor': 'rgb(55,71,79)', 'plot_bgcolor': 'rgb(55,71,79)',
                      'font': {'color': 'rgb(207,217,220)'}, 'legend': {'orientation': 'h', 'y': 1.02, 'yanchor': 'bottom'}}

            plotlyfig = go.Figure(data=traces, layout=layout)
            #py.image.save_as(plotlyfig, filename='./plots/' + system + '_history.png')

            if webpublishing:
                trycounter = 1
                while trycounter < 6:
                    try:
                        print ('Attempting to publish '+system +'_history, attempt #'+str(trycounter))
                        url_name = py.plot(plotlyfig,filename=system + '_history', auto_open=False)
                        published_plots.append(url_name)
                        trycounter = 6
                    except:
                        print ('Failed to publish '+system+'_history')
                        print ('Waiting for 30 s ...')
                        print time.sleep(30)
                        trycounter += 1

            #plotly.offline.plot(plotlyfig, filename='./plots/'+ system + '_history.html', auto_open=False)


        self.fn_save_object(published_plots,'./plots/published_plots.dat')

        return published_plots

    def fn_pull_data_from_eddb(self, target_id=14271):
        # Canonn faction ID is 14271

        # method from https://stackoverflow.com/questions/32400867/pandas-read-csv-from-url to deal with SSL sites
        url = 'https://eddb.io/archive/v5/systems_populated.json'
        s = requests.get(url).content
        systems_populated = pd.read_json(io.StringIO(s.decode('utf-8')))
        #systems_populated = pd.read_json('https://eddb.io/archive/v5/systems_populated.json')
        #systems_populated = pd.read_json('~/Desktop/systems_populated.json')

        url = 'https://eddb.io/archive/v5/factions.json'
        s = requests.get(url).content
        factions = pd.read_json(io.StringIO(s.decode('utf-8')))
        #factions = pd.read_json('https://eddb.io/archive/v5/factions.json')
        #factions = pd.read_json('~/Desktop/factions.json')

        # setup dataframes for extracting systems in which Canonn is present and
        # reduce the faction dataframe to entries only for factions that are in Canonn space

        systems_populated.set_index("name", inplace=True)
        factions.set_index('id', inplace=True)
        system_names_target = []
        faction_names_target = [target_id]

        for system in systems_populated.index:

            # factions presence is list of dictionaries
            factions_present = systems_populated.loc[system, 'minor_faction_presences']
            for faction in factions_present:

                # in some systems, the minor_factions_presences entries is not a directory but a list of directories
                # with possible invalid entries
                # TODO: follow up on those instances and see if the different format is intentional

                if isinstance(faction, dict):
                    if faction['minor_faction_id'] == target_id:
                        system_names_target.append(system)
                        for otherfaction in factions_present:
                            if isinstance(otherfaction, dict):
                                if otherfaction['minor_faction_id'] not in faction_names_target:
                                    faction_names_target.append(otherfaction['minor_faction_id'])
                    # else:
                        # print 'Cannot read data for: ', system

        # filter initial json files by identified systems and faction names
        systems_target = systems_populated.loc[system_names_target]
        factions_target = factions.loc[faction_names_target]

        # add systems and factions Pandas frame as long as it is new

        if self.factionstat == [] or not (self.factionstat[-1][1].equals(systems_target)
                                          and self.factionstat[-1][2].equals(factions_target)):
            self.factionstat.append([time.asctime(), systems_target, factions_target])

    def fn_save_object(self, obj, filename):

        fi = open(filename, "w")
        pickle.dump(obj, fi)
        fi.close()

    def fn_save_data(self):
        # save all data before exit

        self.fn_save_object(self.factionstat, './statdata/factionstat.dat')


# main program from command line

if __name__ == '__main__':

    factionstats = FactionStats()
    #factionstats.fn_pull_data_from_eddb()
    #factionstats.fn_save_data()
    factionstats.fn_plot_system_history(webpublishing=True)
