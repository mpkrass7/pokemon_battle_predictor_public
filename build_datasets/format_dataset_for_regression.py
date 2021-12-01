import numpy as np
import pandas as pd
from logzero import logger

# Much of the preprocessing code lovingly borrowed from a friendly kaggler: https://www.kaggle.com/balams/pokemon-regression-model-beginners/notebook


def read_data():
    pokemon = pd.read_csv("data/pokemon.csv").rename(columns={"#": "index"})
    combat = pd.read_csv("data/combats.csv")
    return pokemon, combat


def build_combat_occurence_dataframe(combat):
    # Combat occurences
    # Count occurences where pokemon is first
    FirstCombat = combat.First_pokemon.value_counts().reset_index(name="FirstCombat")
    # Count occurences where pokemon is second
    SecondCombat = combat.Second_pokemon.value_counts().reset_index(name="SecondCombat")
    TotalCombat = pd.merge(FirstCombat, SecondCombat, how="left", on="index")
    # Count total occurences with pokemon
    TotalCombat["TotalMatch"] = TotalCombat["FirstCombat"] + TotalCombat["SecondCombat"]
    return TotalCombat


def build_match_win_dataframe(combat):
    # Match winning details
    FirstWin = (
        combat["First_pokemon"][combat["First_pokemon"] == combat["Winner"]]
        .value_counts()
        .reset_index(name="FirstWin")
    )
    SecondWin = (
        combat["Second_pokemon"][combat["Second_pokemon"] == combat["Winner"]]
        .value_counts()
        .reset_index(name="SecondWin")
    )
    TotalWin = pd.merge(FirstWin, SecondWin, how="left", on="index")
    TotalWin["TotalWin"] = TotalWin["FirstWin"] + TotalWin["SecondWin"]
    return TotalWin


def merge_dataframes(pokemon, combat):
    combat_occurence = build_combat_occurence_dataframe(combat)
    match_win = build_match_win_dataframe(combat)
    pokemon = pokemon.merge(combat_occurence, how="left", on="index")
    pokemon = pokemon.merge(match_win, how="left", on="index")
    return pokemon.drop(columns="index")


def main():
    logger.info("Reading data...")
    pokemon, combat = read_data()
    logger.info("Merging dataframes...")
    pokemon_full_df = merge_dataframes(pokemon, combat)
    pokemon_full_df = pokemon_full_df.assign(
        Multi_Type=np.where(pd.isna(pokemon_full_df["Type 2"]), False, True),
        winning_percentage=np.round(
            pokemon_full_df["TotalWin"] / pokemon_full_df["TotalMatch"] * 100, 2
        ),
    ).drop(columns=["FirstWin", "SecondWin", "TotalWin", "TotalMatch"])
    pokemon_full_df["Type 2"].fillna("Not Applicable", inplace=True)
    logger.info("Saving modeling dataframe...")
    pokemon_full_df.to_csv("data/pokemon_win_rate_regressor - train.csv", index=False)


if __name__ == "__main__":
    main()
