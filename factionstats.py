import os.path
import pandas as pd
import pickle
import time
import matplotlib.pyplot as plt


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

    def fn_plot_system_history(self):
        # Plots the influence history of a given system saves data and plots
        # Format:
        # Time Faction1 Faction2 ...
        # ...  ...      ...      ...
        # ...  ...      ...      ...

        # Create a list of snapshots over the last 90 days

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
                        date = [entry[system]['Last Time Updated'].tolist()[0]]
                    else:
                        nextline.append(0.0)

                data.loc[data.shape[0]] = [date]+nextline

            data.to_csv('./plotdata/' + system + '_history.dat', index=False)

            # Create Plots

            fig, ax = plt.subplots(nrows=1, ncols=1)
            for faction in factionlist:
                ax.plot(data['Date'].tolist(), data[faction].tolist(),'-',label=faction)
            ax.legend()
            ax.set_xlabel('Date')
            ax.set_ylabel('Influence (%)')
            fig.autofmt_xdate()
            fig.suptitle(system)
            fig.savefig('./plots/'+ system + '_history.png')
            plt.close(fig)

    def fn_plot_system_snapshots(self):
        # Creates a file that can be used for plotting system snapshots (most recent time)
        # Format:
        # Faction Influence FactionState LastTimeUpdated
        # ...     ...       ...           ...
        # ...     ...       ...           ...

        snapshot = self.fn_get_system_snapshots(self.factionstat[-1][1], self.factionstat[-1][2])
        for system in snapshot:

            # Create current snapshots and save the data for future plotting

            snapshot[system].sort_index()
            snapshot[system].to_csv('./plotdata/'+system+'_snapshot.dat', index=False)

            # Use matplotlib to create plots

            labels = snapshot[system]['Faction'].tolist()
            sizes = snapshot[system]['Influence'].tolist()
            explode = []
            for name in labels:
                if name == 'Canonn':
                    explode.append(0.1)
                else:
                    explode.append(0.0)

            fig1, ax1 = plt.subplots()
            fig1.suptitle(system+' @ '+str(snapshot[system]['Last Time Updated'].tolist()[0]))
            ax1.pie(sizes, explode=explode, labels=labels, autopct='%1.1f%%',
                    shadow=True, startangle=90)
            ax1.axis('equal')

            fig1.savefig('./plots/'+system+'_snapshot.png')

    def fn_pull_data_from_eddb(self, target_id=14271):
        # Canonn faction ID is 14271

        systems_populated = pd.read_json('https://eddb.io/archive/v5/systems_populated.json')
        # systems_populated = pd.read_json('~/Desktop/systems_populated.json')
        factions = pd.read_json('https://eddb.io/archive/v5/factions.json')
        # factions = pd.read_json('~/Desktop/factions.json')

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
    #factionstats.fn_plot_system_snapshots()
    factionstats.fn_plot_system_history()
