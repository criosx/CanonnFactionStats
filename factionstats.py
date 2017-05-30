import os.path
import pandas as pd
import pickle


class FactionStats:
    def __init__(self):

        if os.path.isfile('factionstat.dat'):
            self.factionstat = self.fn_load_object('factionstat.dat')
        else:
            self.factionstat={}

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

        systems_target = systems_populated.loc[system_names_target]
        factions_target = factions.loc[faction_names_target]

        return systems_target, factions_target

    def fn_save_object(self, object, sFileName):

        File=open(sFileName, "w")
        pickle.dump(object, File)
        File.close()

    def fn_save_data(self):
        # save all data before exit

        self.fn_save_object(self.factionstat, 'factionstat.dat')


# main program from command line

if __name__ == '__main__':

    facinst = FactionStats()
    systems, factions = facinst.fn_pull_data_from_eddb()
    print systems
    print factions
    facinst.fn_save_data()
