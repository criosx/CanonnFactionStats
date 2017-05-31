import os.path
import pandas as pd
import pickle
import time


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

    def fn_load_object(self, sFileName):

        File = open(sFileName, "r")
        Object = pickle.load(File)
        File.close()

        return Object

    def fn_pull_data_from_eddb(self, target_id=14271):
        # Canonn faction ID is 14271

        # systems_populated = pd.read_json('https://eddb.io/archive/v5/systems_populated.json')
        systems_populated = pd.read_json('~/Desktop/systems_populated.json')
        # factions = pd.read_json('https://eddb.io/archive/v5/factions.json')
        factions = pd.read_json('~/Desktop/factions.json')

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
