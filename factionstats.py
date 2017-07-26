import csv
import os.path
import pandas as pd
import datetime
import time
import plotly.plotly as py
import plotly.graph_objs as go
import plotly
import io
from sys import argv
from bs4 import BeautifulSoup
import requests

class FactionStats:
    def __init__(self, target_name, mode=""):

        # load list with stat data from file
        #
        # structure of list is [[str(time), systems pandas dataframe, factions pandas dataframe]]
        # the dataframes are pandas frames converted from the EDDB json dumps after elimination of all entries
        # not relevant to the faction
        #
        # factionstat is expanded daily from the EDDB dump, saved in the standard file
        # more frequently, the EDDB webpage is being checked for changes, but those changes are only stored
        # in a temporary file _update until the next dump is available

        filename = './statdata/factionstat_'+target_name+'.csv'
        filename_update = './statdata/factionstat_'+target_name+'_update.csv'

        if mode == "update":
            if os.path.isfile(filename_update):
                self.factionstat = self.fn_load_factionstat(target_name, mode=mode)
                return

        # even if mode=="update" but no updated file was found, load the standard file
        if os.path.isfile(filename):
            # self.factionstat = self.fn_load_object('./statdata/factionstat_'+target_name+'.dat')
            self.factionstat = self.fn_load_factionstat(target_name)

            if mode == "update":
                # duplicate last entry in factionstats when starting temporary file from standard
                self.factionstat.append(self.factionstat[-1][:])
            else:
                # if temporary update exist but standard was loaded, then delete temporary file
                if os.path.isfile(filename_update):
                    os.remove(filename_update)
        else:
            print ('Did not find stat file for '+target_name)
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

    def fn_plot_system_history(self, target_name, webpublishing=False):
        # Plots the influence history of a given system saves data and plots
        # Format:
        # Time Faction1 Faction2 ...
        # ...  ...      ...      ...
        # ...  ...      ...      ...

        # Create a list of snapshots over the last 90 days

        py.sign_in('criosix','3jLviaVFikQOH1BZRcew')
        published_plots = []

        history = []
        for entry in self.factionstat:
            if (time.time()-time.mktime(time.strptime(entry[0]))) < (90*24*60*60+1):
                history.append(self.fn_get_system_snapshots(entry[1], entry[2]))

        # Get a list of all occupied systems
        systemlist = []
        for entry in history:
            for system in entry:
                if system not in systemlist:
                    systemlist.append(system)
        systemlist.sort()

        # Create data and plots for all systems
        target_faction_overview_traces=[]
        for system in systemlist:

            # Get list of all factions
            factionlist = []
            for entry in history:
                if system in entry.keys():
                    for faction in entry[system]['Faction'].tolist():
                        if faction not in factionlist:
                            factionlist.append(faction)

            # Create Data
            factionlist.sort()
            headerline = ['Date']+factionlist
            data = pd.DataFrame(columns=headerline)
            markers = pd.DataFrame(columns=headerline)

            last_date = ''
            for entry in history:
                if system in entry.keys():

                    # keep last history entry with target faction present as snapshot
                    snapshot = entry

                    nextline_influence = []
                    nextline_markers = []
                    for faction in factionlist:
                        if faction in entry[system]['Faction'].tolist():
                            i = entry[system]['Faction'].tolist().index(faction)
                            nextline_influence.append(entry[system]['Influence'].tolist()[i])
                            nextline_markers.append(entry[system]['Faction State'].tolist()[i])
                            date = entry[system]['Last Time Updated'].tolist()[0]
                        else:
                            nextline_influence.append(0.0)
                            nextline_markers.append('')

                    if date != last_date:
                        for i, element in enumerate(nextline_markers):
                            if element == 'None':
                                nextline_markers[i] = ''

                        last_date = date

                        data.loc[data.shape[0]] = [date]+nextline_influence
                        markers.loc[markers.shape[0]] = [date]+nextline_markers

            data.to_csv('./plotdata/' + system + '_history.dat', index=False)
            markers.to_csv('./plotdata/' + system + '_markers.dat', index=False)

            # Create Plots with Plotly
            # Create current snapshot plot using last snapshot with target faction present as found above

            snapshot[system].sort_index()
            snapshot[system].to_csv('./plotdata/'+system+'_snapshot.dat', index=False)

            labels = snapshot[system]['Faction'].tolist()
            pull = []
            color = []
            for i, val in enumerate(labels):
                if snapshot[system]['Faction State'].tolist()[i] != 'None':
                    labels[i] = val + ' (' + snapshot[system]['Faction State'].tolist()[i] + ')'
                if val == target_name:
                    pull.append(0.05)
                    color.append('cornflowerblue')
                else:
                    pull.append(0.0)
                    color.append('')
            if system == 'Mobia':
                pass
            values = snapshot[system]['Influence'].tolist()
            values_round = []
            for i,element in enumerate(values):
                if isinstance(element, (int, long, float, complex)):
                    values_round.append(round(element, 1))
                else:
                    values_round.append(0.0)
            centertext = str(snapshot[system]['Last Time Updated'].tolist()[0]).split()[0]+'<br>' + \
                         str(snapshot[system]['Last Time Updated'].tolist()[0]).split()[1]

            # if snapshot is too old, change color of center text of pie chart
            # centertextcolor = 'rgb(207,217,220)'
            centertextcolor = 'lightgreen'
            if (time.time() - time.mktime(time.strptime(str(snapshot[system]['Last Time Updated'].tolist()[0]),
                                                       '%Y-%m-%d %H:%M:%S'))) > (1 * 24 * 60 * 60 + 1):
                centertextcolor = 'yellow'
            if (time.time() - time.mktime(time.strptime(str(snapshot[system]['Last Time Updated'].tolist()[0]),
                                                       '%Y-%m-%d %H:%M:%S'))) > (2 * 24 * 60 * 60 + 1):
                centertextcolor = 'red'

            layout = {'annotations': [{"font": {'color': centertextcolor}, "showarrow": False, "text": centertext}],
                      'paper_bgcolor': 'rgb(55,71,79)', 'plot_bgcolor': 'rgb(55,71,79)',
                      'font': {'color': 'rgb(207,217,220)'}, 'legend': {'orientation': 'h'}, 'autosize': True}

            pietrace = go.Pie(labels=labels, values=values_round, hoverinfo="label+percent", hole=.4, pull=pull,
                              marker=dict(colors=color))
            plotlyfig = go.Figure(data=[pietrace], layout=layout)

            # py.image.save_as(plotlyfig, filename='./plots/' + system + '_snapshot.png')

            if webpublishing:
                trycounter = 1
                while trycounter < 6:
                    try:
                        print ('Publishing '+system + '_snapshot, attempt #'+str(trycounter))
                        url_name = py.plot(plotlyfig,filename=target_name+'/'+system + '_snapshot', auto_open=False)
                        published_plots.append(system + '_snapshot:    ' + url_name + '\n')
                        trycounter = 6
                    except:
                        print ('Failed to publish '+system+'_history')
                        print ('Waiting for 30 s ...')
                        print time.sleep(30)
                        trycounter += 1

            # History
            traces = []
            for faction in factionlist:

                ydata = data[faction].tolist()
                ydata_round = []
                for i, element in enumerate(ydata):
                    if isinstance(element, (int, long, float, complex)):
                        ydata_round.append(round(element, 1))
                    else:
                        ydata_round.append(0.0)

                # faction state marker data can contain missing elements
                # check for those and substitute '' for faction state
                text_markers = markers[faction].tolist()
                for i, element in enumerate(text_markers):
                    if pd.isnull(element):
                        text_markers[i]=''

                # go through the faction state markers for the plot and mark only the start
                # and end of a state

                current_state = ''
                for i, marker in enumerate(text_markers):
                    if current_state == '' and marker != '':
                        current_state = marker
                        text_markers[i] = marker + ' start'
                        if len(text_markers) > (i+1) and text_markers[i+1] != current_state:
                            current_state = ''
                            text_markers[i] = text_markers[i] + ' + end'
                    elif current_state == '' and marker == '':
                        pass
                    elif current_state != marker:
                        # sudden change in state without state ended
                        current_state = marker
                        text_markers[i] = marker + ' start'
                        if len(text_markers) > (i+1) and text_markers[i+1] != current_state:
                            current_state = ''
                            text_markers[i] = text_markers[i] + ' + end'
                    elif current_state == marker and len(text_markers) > (i+1):
                        if text_markers[i+1] != current_state:
                            text_markers[i] = current_state + ' end'
                            current_state = ''
                        else:
                            text_markers[i] = ''

                # visually mark beginning and end of faction states using different symbol sizes
                size = []
                for element in text_markers:
                    if (' start' not in element) and (' end' not in element):
                        size.append(5)
                    else:
                        size.append(9)

                if faction == target_name:
                    width = 3
                    color = 'cornflowerblue'
                    trace = go.Scatter(x=data['Date'].tolist(), y=ydata_round, mode='lines+markers'
                                       , name=faction, line=dict(shape='spline', width=width, color=color),
                                       text=text_markers, marker=dict(size=size, line=dict(width=0), symbol='circle'))
                    target_faction_overview_traces.append(go.Scatter(x=data['Date'].tolist(), y=ydata_round,
                                                                     mode='lines+markers', name=system,
                                                                     line=dict(shape='spline', width=2),
                                       text=text_markers, marker=dict(size=size, line=dict(width=0), symbol='circle')))
                else:
                    width = 2
                    trace = go.Scatter(x=data['Date'].tolist(), y=ydata_round, mode='lines+markers',
                                       name=faction, line=dict(shape='spline', width=width),
                                       text=text_markers, marker=dict(size=size, line=dict(width=0), symbol='circle'))

                traces.append(trace)

            layout = {'xaxis': {'title': 'Date', 'mirror': True, 'showline': True, 'color': 'rgb(207,217,220)',
                                'rangeselector': {'font': {'color': 'rgb(0,0,0)'}, 'x': 1.00, 'xanchor': 'right',
                                                  'buttons': [{'count': 14, 'label': '14d', 'step': 'day',
                                                               'stepmode': 'backward'},
                                                              {'count': 1, 'label': '1m', 'step': 'month',
                                                               'stepmode': 'backward'},
                                                              {'step': 'all'}]}},
                      'yaxis': {'title': 'Influence (%)', 'mirror': True, 'showline': True, 'color': 'rgb(207,217,220)'},
                      'paper_bgcolor': 'rgb(55,71,79)', 'plot_bgcolor': 'rgb(55,71,79)',
                      'font': {'color': 'rgb(207,217,220)'}, 'legend': {'orientation': 'h', 'y': 1.05, 'yanchor': 'bottom'}}

            plotlyfig = go.Figure(data=traces, layout=layout)
            # py.image.save_as(plotlyfig, filename='./plots/' + system + '_history.png')

            if webpublishing:
                trycounter = 1
                while trycounter < 6:
                    try:
                        print ('Publishing '+system +'_history, attempt #'+str(trycounter))
                        url_name = py.plot(plotlyfig,filename=target_name+'/'+system + '_history', auto_open=False)
                        published_plots.append(system + '_history:    '+url_name+'\n')
                        trycounter = 6
                    except:
                        print ('Failed to publish '+system+'_history')
                        print ('Waiting for 30 s ...')
                        print time.sleep(30)
                        trycounter += 1

            # plotly.offline.plot(plotlyfig, filename='./plots/'+ system + '_history.html', auto_open=False)

        layout = {'xaxis': {'title': 'Date', 'mirror': True, 'showline': True, 'color': 'rgb(207,217,220)',
                            'rangeselector': {'font': {'color': 'rgb(0,0,0)'}, 'x': 1.00, 'xanchor': 'right',
                                              'buttons': [{'count': 14, 'label': '14d', 'step': 'day',
                                                           'stepmode': 'backward'},
                                                          {'count': 1, 'label': '1m', 'step': 'month',
                                                           'stepmode': 'backward'},
                                                          {'step': 'all'}]}},
                  'yaxis': {'title': 'Influence (%)', 'mirror': True, 'showline': True, 'color': 'rgb(207,217,220)'},
                  'paper_bgcolor': 'rgb(55,71,79)', 'plot_bgcolor': 'rgb(55,71,79)',
                  'font': {'color': 'rgb(207,217,220)'}, 'legend': {'orientation': 'h', 'y': 1.05, 'yanchor': 'bottom'}}

        plotlyfig = go.Figure(data=target_faction_overview_traces, layout=layout)

        if webpublishing:
            trycounter = 1
            while trycounter < 6:
                try:
                    print ('Publishing ' + target_name + '_influence_overview, attempt #' + str(trycounter))
                    url_name = py.plot(plotlyfig, filename=target_name + '/influence_overview', auto_open=False)
                    published_plots.append(target_name + '_influence_overview:    ' + url_name + '\n')
                    trycounter = 6
                except:
                    print ('Failed to publish ' + target_name + '_influence_overview')
                    print ('Waiting for 30 s ...')
                    print time.sleep(30)
                    trycounter += 1

        # plotly.offline.plot(plotlyfig, filename='./plots/'+ target_name + '_influence_overview.html', auto_open=False)

        fi = open('./plots/published_plots'+target_name+'.dat', 'w')
        fi.writelines(published_plots)
        fi.close()

        return published_plots

    def fn_pull_data_from_json(self, target_name):

        systems_populated = pd.read_json('./jsondata/systems_populated.json')
        factions = pd.read_json('./jsondata/factions.json')

        # setup dataframes for extracting systems in which the target faction is present and
        # reduce the faction dataframe to entries only for factions that are in target faction's space
        systems_populated.set_index("name", inplace=True)
        factions.set_index('id', inplace=True)

        # find the target name in the factions data frame and retrieve ID
        found_id = False
        for id in factions.index.tolist():
            if target_name == factions.loc[id, 'name']:
                target_id = id
                found_id = True
                break

        if not found_id:
            print 'Did not find target faction in EDDB dump'
            return False

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

        return True

    def fn_save_factionstat(self, target_name, mode=''):
        modestr = ''
        if mode == 'update':
            modestr = '_update'

        with open('./statdata/factionstat_' + target_name + modestr + '.csv', 'w') as handle:
            writer = csv.writer(handle, lineterminator='\n')
            for entry in self.factionstat:
                writer.writerow([entry[0]])
                entry[1].to_json('./statdata/systems_'+target_name+'_'+entry[0]+ modestr + '.json')
                entry[2].to_json('./statdata/factions_'+target_name+'_'+entry[0]+ modestr + '.json')

    def fn_load_factionstat(self, target_name, mode=''):
        result = []
        modestr = ''
        if mode == 'update':
            modestr = '_update'

        with open('./statdata/factionstat_' + target_name + modestr + '.csv', 'rb') as handle:
            reader = csv.reader(handle)
            for row in reader:
                date = row[0]
                systems = pd.read_json('./statdata/systems_'+target_name+'_'+date + modestr + '.json')
                factions = pd.read_json('./statdata/factions_'+target_name+'_'+date + modestr + '.json')
                #systems.set_index("name", inplace=True)
                #factions.set_index('id', inplace=True)

                result.append([date, systems, factions])
        return result

    def fn_update(self, target_name):

        def isfloat(value):
            try:
                float(value)
                return True
            except:
                return False


        global_update = False

        systems = self.factionstat[-1][1].copy(deep=False)
        factions = self.factionstat[-1][2].copy(deep=False)

        found_id = False
        for faction_id in factions.index.tolist():
            if target_name == factions.loc[faction_id, 'name']:
                target_id = faction_id
                found_id = True
                break

        if not found_id:
            print 'Did not find target faction in saved data. Cannot update.'
            return False


        url = 'https://eddb.io/faction/'+ str(target_id)
        htmlContent = requests.get(url, verify=False)
        soup = BeautifulSoup(htmlContent.text, 'html.parser')

        entries = soup.find_all("tr", ["systemRow", "systemFactionRow"])


        # The entries are currently in the following format when using .stripped_strings
        #
        # systemFactionRow:
        #
        # u'92.7%'
        # u'Canonn'
        # u'Independent'
        # u'Cooperative'
        # u'Expansion'
        # u'Chacobog'
        # u'Controlling'
        #
        # systemRow:
        #
        # u'Chacobog'
        # u'Security:'
        # u'Medium'
        # u'State:'
        # u'Boom'
        # u'Population:'
        # u'2,298,725'
        # u'Power:'
        # u'None'
        # u'178.92'
        # u'ly from Sol'
        # u'Update: 10 hours'

        system = ''
        factions_present = []
        recentupdate = False
        # parse web page line by line
        for entry in entries:

            # parse current web page line into list of strings
            elementlist = []
            for element in entry.stripped_strings:
                elementlist.append(element)
            # look for next system line
            if elementlist[0] in systems.index:
                system = elementlist[0]
                delta_t = 0
                resolution = ''
                recentupdate = True
                updated = elementlist[-1].replace("Update:","")
                if 'hours' in updated:
                    delta_t = datetime.timedelta(hours = int(updated.replace("hours","")))
                    resolution = 'h'
                elif 'hour' in updated:
                    delta_t = datetime.timedelta(hours = int(updated.replace("hour","")))
                    resolution = 'h'
                elif 'mins' in updated:
                    delta_t = datetime.timedelta(minutes = int(updated.replace("mins","")))
                    resolution = 'min'
                elif 'min' in updated:
                    delta_t = datetime.timedelta(minutes = int(updated.replace("min","")))
                    resolution = 'min'
                else:
                    recentupdate = False
                    resolution = 'd'

                if resolution != 'd':
                    update_estimate = datetime.datetime.fromtimestamp(time.time()+time.timezone).replace(microsecond=0) \
                                  - delta_t
                    last_update = systems.loc[system,'updated_at']
                    dif = update_estimate - last_update
                    if resolution == 'min':
                        if dif.total_seconds() < 1*60:
                            recentupdate = False
                    if resolution == 'h':
                        if dif.total_seconds() < 60*60:
                            recentupdate = False

                if recentupdate:
                    factions_present = systems.loc[system, 'minor_faction_presences']
                    global_update = True

            # otherwise check for next faction in the same system, but only when recent update in system detected
            elif recentupdate:
                #first entry should be faction influence, check for number
                first = elementlist[0].replace("%","")
                if isfloat(first):
                    influence = round(float(first),1)
                    name = elementlist[1]
                    state = elementlist[4]

                    for faction in factions_present:
                        factionname = factions.loc[faction['minor_faction_id'], 'name']
                        if factionname == name:
                            faction['influence'] = influence
                            faction['state'] = state
                            systems.loc[system,'updated_at'] = update_estimate
                            break

        return global_update


def fn_update_from_eddb():
    def fn_download_from_ssl(url):
        try:
            # method from https://stackoverflow.com/questions/32400867/pandas-read-csv-from-url
            # to deal with SSL sites, mostly for MacOS
            s = requests.get(url).content
            frame = pd.read_json(io.StringIO(s.decode('utf-8')))
        except:
            # standard method
            frame = pd.read_json('https://eddb.io/archive/v5/systems_populated.json')
        return frame

    systems_populated = fn_download_from_ssl('https://eddb.io/archive/v5/systems_populated.json')
    systems_populated.to_json('./jsondata/systems_populated.json')
    factions = fn_download_from_ssl('https://eddb.io/archive/v5/factions.json')
    factions.to_json('./jsondata/factions.json')

# main program from command line

if __name__ == '__main__':

    webpublishing = True
    targetlist = ['Canonn', 'Canonn Deep Space Research']

    if len(argv) == 1:

        # Download lates EDDB dump only once
        fn_update_from_eddb()

        for target_name in targetlist:
            # Create oject and load previous factionstat data if existent
            factionstats = FactionStats(target_name)
            # Add recent and new faction data from current dump to factionstat
            factionstats.fn_pull_data_from_json(target_name)
            # Save factionstat
            factionstats.fn_save_factionstat(target_name)
            # Plot from factionstat
            factionstats.fn_plot_system_history(target_name, webpublishing=webpublishing)

    elif argv[1] == '-update':

        for target_name in targetlist:
            # Create oject and load previous factionstat data if existent
            factionstats = FactionStats(target_name, mode='update')
            # only plot if there are updates
            if factionstats.fn_update(target_name):
                factionstats.fn_save_factionstat(target_name, mode='update')
                factionstats.fn_plot_system_history(target_name, webpublishing=webpublishing)

