import numpy as np
import pandas as pd
from logzero import logger

CONTINUOUS_COLUMNS = [
    "hp",
    "attack",
    "defense",
    "sp_attack",
    "sp_defense",
    "speed",
]

TYPE_ADVANTAGES = {
    "fire": ["grass", "ice", "bug", "steel", "fairy"],
    "grass": ["water", "ground", "rock"],
    "water": ["fire", "ground", "rock"],
    "electric": ["water", "flying"],
    "ice": ["grass", "ground", "flying", "dragon"],
    "psychic": ["poison", "fighting",],
    "fighting": ["normal", "ice", "rock", "dark", "steel"],
    "normal": [],
    "poison": ["grass", "fairy"],
    "bug": ["grass", "psychic", "dark"],
    "dragon": ["dragon"],
    "dark": ["psychic", "ghost"],
    "fairy": ["fighting", "dragon", "dark"],
    "rock": ["fire", "ice", "flying", "bug"],
    "ghost": ["ghost", "psychic"],
    "steel": ["ice", "rock", "fairy"],
    "ground": ["rock", "fire", "electric", "poison"],
    "flying": ["grass", "fighting", "bug"],
}


def read_data():
    pokemon = pd.read_csv("../data/pokemon.csv")
    pokemon.columns = [
        "id",
        "name",
        "type_1",
        "type_2",
        "hp",
        "attack",
        "defense",
        "sp_attack",
        "sp_defense",
        "speed",
        "generation",
        "legendary",
    ]
    combat = pd.read_csv("../data/combats.csv")
    combat_test = pd.read_csv("../data/tests.csv")
    return pokemon, combat, combat_test


def process_data(combat, pokemon, is_training_data=True):
    pokemon = pokemon.assign(
        Multi_Type=np.where(pd.isna(pokemon["type_2"]), False, True),
        type_2=np.where(pd.isna(pokemon["type_2"]), "None", pokemon["type_2"]),
    )
    pokemon1 = pokemon.copy()
    pokemon2 = pokemon.copy()
    pokemon1.columns = ["id"] + ["pokemon_1_" + c for c in pokemon1.columns[1:]]
    pokemon2.columns = ["id"] + ["pokemon_2_" + c for c in pokemon2.columns[1:]]
    combat_full = combat.merge(
        pokemon1, how="left", left_on=["First_pokemon"], right_on=["id"], validate="m:1"
    )
    combat_full = combat_full.merge(
        pokemon2,
        how="left",
        left_on=["Second_pokemon"],
        right_on=["id"],
        validate="m:1",
    ).drop(columns=["id_x", "id_y"])

    for stat in CONTINUOUS_COLUMNS:
        combat_full[f"net_{stat}"] = (
            combat_full[f"pokemon_1_{stat}"] - combat_full[f"pokemon_2_{stat}"]
        )

    if is_training_data:
        combat_full["pokemon_1_won"] = np.where(
            combat_full["First_pokemon"] == combat_full["Winner"], True, False
        )
    return combat_full


def build_type_advantage(df):
    temp = (
        df[
            [
                "pokemon_1_type_1",
                "pokemon_1_type_2",
                "pokemon_2_type_1",
                "pokemon_2_type_2",
            ]
        ]
        .copy()
        .fillna("none")
    )
    for col in temp.columns:
        temp[col] = temp[col].str.lower()

    t11, t12, t21, t22 = (
        temp.pokemon_1_type_1,
        temp.pokemon_1_type_2,
        temp.pokemon_2_type_1,
        temp.pokemon_2_type_2,
    )

    t_adv = []
    for h, i, j, k in zip(t11, t12, t21, t22):
        counter = 3
        advantage_types = list(
            set(TYPE_ADVANTAGES[h] + TYPE_ADVANTAGES.get(i, ["none"]))
        )
        disadvantage_types = list(
            set(TYPE_ADVANTAGES[j] + TYPE_ADVANTAGES.get(k, ["none"]))
        )
        if j in advantage_types:
            counter += 1
        if k in advantage_types:
            counter += 1
        if h in disadvantage_types:
            counter -= 1
        if i in disadvantage_types:
            counter -= 1
        t_adv.append(counter)

    return t_adv


def main():
    logger.info("Reading data...")
    pokemon, combat, test_data = read_data()
    logger.info("Processing training data...")
    training_data = process_data(combat, pokemon)
    training_data["type_advantage"] = build_type_advantage(training_data)
    scoring_data = process_data(test_data, pokemon, is_training_data=False)
    scoring_data["type_advantage"] = build_type_advantage(scoring_data)

    logger.info("Saving data...")
    training_data.to_csv("../data/pokemon_combat_classifier - train.csv", index=False)
    scoring_data.to_csv("../data/pokemon_combat_classifier - test.csv", index=False)


if __name__ == "__main__":
    main()

