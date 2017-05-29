import pandas as pd


def fn_pull_data_from_eddb():
    systems_populated = pd.read_json('https://eddb.io/archive/v5/systems_populated.json')
    factions = pd.read_json('https://eddb.io/archive/v5/factions.json')

    # Canonn faction ID is 14271

    systems_populated.set_index("name", inplace=True)
    system_names_canonn = []
    for system in systems_populated.index:
        # factions presence is list of dictionaries
        factions_present = systems_populated.loc[system, 'minor_factions_presences']
        for faction in factions_present:
            if faction['minor_faction_id'] == 14271:
                system_names_canonn.append(system)

    systems_canonn = systems_populated.loc[system_names_canonn]

