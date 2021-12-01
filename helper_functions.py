import pandas as pd
import plotly.express as px
import numpy as np
import streamlit as st
from logzero import logger

import get_predictions as gp
from get_predictions import DEPLOYMENT_ID
from build_datasets.format_dataset_for_classification import (
    process_data,
    CONTINUOUS_COLUMNS,
)


# from get_predictions import DICT_RECATEGORIZE

SMALL_FONT_STYLE = """
    <style>
    .small-font {
        font-size:14px;
        font-style: italic;
        color: #b1a7a6;
    }
    </style>
    """

POKEMON_BASE_COLUMNS = [
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
    "ghost": ["ghost", "psychic", "normal"],
    "steel": ["ice", "rock", "fairy"],
    "ground": ["rock", "fire", "electric", "poison"],
    "flying": ["grass", "fighting", "bug"],
    "none": [],
}


@st.cache
def load_data():
    # scored_data = pd.read_csv("data/pokemon_combat_classifier - train.csv")
    pokemon_data = pd.read_csv("data/pokemon.csv")
    pokemon_data.columns = POKEMON_BASE_COLUMNS

    return pokemon_data


def get_dropdowns(df):
    pokemon1 = df.name
    pokemon2 = pokemon1.copy()

    types = df.type_1.unique()
    return pokemon1, pokemon2, types


def build_comp_chart(pokemon_data, pokemon1, pokemon2):
    pokemon_comp = (
        pokemon_data.loc[lambda x: x.name.isin([pokemon1, pokemon2])]
        .assign(sort_order=lambda x: np.where(x.name == pokemon1, 0, 1))
        .sort_values(by="sort_order")
        .drop(columns="sort_order")
        .copy()
    )
    pokemon_comp.columns = POKEMON_BASE_COLUMNS

    melt_comp = (
        pokemon_comp[
            [
                "id",
                "name",
                "hp",
                "attack",
                "defense",
                "sp_attack",
                "sp_defense",
                "speed",
            ]
        ]
        .melt(id_vars=["name", "id"], var_name="stat", value_name="value")
        .rename(columns={"name": "Pokemon"})
    )

    fig = px.bar(melt_comp, x="stat", y="value", color="Pokemon", barmode="group",)

    fig.update_layout(
        yaxis_title=None,
        xaxis_title=None,
        autosize=False,
        height=500,
        width=1200,
        font=dict(size=22,),
    )
    return fig


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


def process_for_pokemon_battle(pokemon_df, pokemon1, pokemon2):
    pokemon1_id = pokemon_df.loc[pokemon_df.name == pokemon1].id.values[0]
    pokemon2_id = pokemon_df.loc[pokemon_df.name == pokemon2].id.values[0]
    combat = pd.DataFrame(
        {"First_pokemon": [pokemon1_id], "Second_pokemon": [pokemon2_id]}
    )
    battle_data = process_data(combat, pokemon_df, is_training_data=False)
    battle_data["type_advantage"] = build_type_advantage(battle_data)
    outpath = "data/temp_battle_data.csv"
    battle_data.to_csv(outpath, index=False)
    return outpath


def run_pokemon_battle(battle_ready_df):
    preds = gp.main(battle_ready_df, DEPLOYMENT_ID)
    probability_pokemon1_wins = preds.predictionValue[0]
    return probability_pokemon1_wins, preds


def process_for_custom_battle(pokemon_df, pokemon2, custom_pokemon_dict):
    custom_pokemon_dict["pokemon_1_Multi_Type"] = (
        1
        if (
            custom_pokemon_dict["pokemon_1_type_1"]
            and custom_pokemon_dict["pokemon_1_type_2"]
        )
        else 0
    )

    pokemon2_df = pokemon_df.loc[pokemon_df.name == pokemon2]
    logger.info(pokemon2_df.columns)

    pokemon2_df.columns = [f"pokemon_2_{i}" for i in pokemon2_df.columns]

    pokemon2_df_dict = pokemon2_df.to_dict("row")[0]
    pokemon2_df_dict["pokemon_2_Multi_Type"] = (
        1
        if (
            pokemon2_df_dict["pokemon_2_type_1"]
            and pokemon2_df_dict["pokemon_2_type_2"]
        )
        else 0
    )

    for key, value in pokemon2_df_dict.items():
        pokemon2_df_dict[key] = [value]

    combine_dict = {**pokemon2_df_dict, **custom_pokemon_dict}
    battle_data = pd.DataFrame(combine_dict)

    battle_data["type_advantage"] = build_type_advantage(battle_data)

    for stat in CONTINUOUS_COLUMNS:
        battle_data[f"net_{stat}"] = (
            battle_data[f"pokemon_1_{stat}"] - battle_data[f"pokemon_2_{stat}"]
        )

    outpath = "data/temp_battle_data.csv"
    battle_data.to_csv(outpath, index=False)
    return outpath
