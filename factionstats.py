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
            self.factionstat=[]

    def fn_add_data(self, systems, factions):
        # add systems and factions Pandas frame as long as it is new
        # time stamp is just for object inspection purposes, does not check when the previous
        # entry to the stat data list was appended

        if self.factionstat == [] or \
                not (self.factionstat[-1][1].equals(systems) and self.factionstat[-1][2].equals(factions)):
            self.factionstat.append([time.asctime(), systems, factions])

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
                fInfluence = faction['influence']
                strState = faction['state']
                Updated = systems.loc[system, 'updated_at']
                strFaction = factions.loc[faction['minor_faction_id'],'name']
                data.loc[data.shape[0]]=[strFaction, fInfluence, strState, Updated]
            snapshot[system] = data.copy()

        return snapshot

    def fn_load_object(self, sFileName):

        File = open(sFileName, "r")
        Object = pickle.load(File)
        File.close()

        return Object

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

            labels= snapshot[system]['Faction'].tolist()
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

        return systems_target, factions_target

    def fn_save_object(self, object, sFileName):

        File=open(sFileName, "w")
        pickle.dump(object, File)
        File.close()

    def fn_save_data(self):
        # save all data before exit

        self.fn_save_object(self.factionstat, './statdata/factionstat.dat')


# main program from command line

if __name__ == '__main__':

    factionstats = FactionStats()
    systems, factions = factionstats.fn_pull_data_from_eddb()
    factionstats.fn_add_data(systems,factions)
    factionstats.fn_save_data()
    factionstats.fn_plot_system_snapshots()
