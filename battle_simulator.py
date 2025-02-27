import streamlit as st
from logzero import logger
import helper_functions as hf


# padding = 0
st.set_page_config(page_title="Pokemon Battle Simulator", layout="wide", page_icon="⚔️")

st.markdown(
    hf.SMALL_FONT_STYLE,
    unsafe_allow_html=True,
)

pokemon = hf.load_data()
median_stats = dict(
    pokemon[["hp", "speed", "attack", "defense", "sp_attack", "sp_defense"]]
    .median()
    .astype(int)
)

pokemon_dropdown1, pokemon_dropdown2, types = hf.get_dropdowns(pokemon)
title, icon = st.columns([4, 2])
title.title("Welcome to the Pokemon Battle Simulator")
icon.image("images/datarobot_icon.png", width=150)

st.write(
    """
    Select two Pokemon. 
    Their information will be shown along with their base stats.
    Click "Run" on the left hand side of the screen to see who will win in a battle.
    Data downloaded from https://www.kaggle.com/terminus7/pokemon-challenge.
    I take no responsibility for shitty training data on battle results.
    """
)

pokemon_box1, _, pokemon_box2, _ = st.columns([3, 1, 3, 5])
pokemon1 = pokemon_box1.selectbox("Pokemon 1", pokemon_dropdown1, index=30)
pokemon2 = pokemon_box2.selectbox("Pokemon 2", pokemon_dropdown2, index=4)
press_battle_button = st.button("Run")

st.plotly_chart(hf.build_comp_chart(pokemon, pokemon1, pokemon2))


battle_loc, battle_image, _, battle_explanation = st.columns([5, 2, 1, 4])


# battle_loc.subheader(f"And the winner between {pokemon1} and {pokemon2} is: ")


# hf.display()
# table_loc.table(hf.display_table(scored_data.head(10)))

if press_battle_button > 0:

    prep_for_battle = hf.process_for_pokemon_battle(pokemon, pokemon1, pokemon2)
    battle_results, preds = hf.run_pokemon_battle(
        prep_for_battle,
    )

    winner = pokemon1 if battle_results > 0.5 else pokemon2
    try:
        battle_image.image(
            f"images/{winner.lower()}.png",
            width=250,
        )
    except Exception as e:
        logger.warning(e)
    battle_loc.subheader(
        f"And the winner between {pokemon1} and {pokemon2} is: {winner}!"
    )
    explanation_1 = f"{preds['EXPLANATION_1_FEATURE_NAME'][0].replace('_', ' ').upper()} {preds['EXPLANATION_1_QUALITATIVE_STRENGTH'][0]}"
    explanation_2 = f"{preds['EXPLANATION_2_FEATURE_NAME'][0].replace('_', ' ').upper()} {preds['EXPLANATION_2_QUALITATIVE_STRENGTH'][0]}"
    explanation_3 = f"{preds['EXPLANATION_3_FEATURE_NAME'][0].replace('_', ' ').upper()} {preds['EXPLANATION_3_QUALITATIVE_STRENGTH'][0]}"
    battle_explanation.markdown(
        f"""
            <h3>Primary Drivers:</h3> \n
            <p style="font-family:Courier; font-size: 20px;">{explanation_1}</p> \n
            <p style="font-family:Courier; font-size: 20px;">{explanation_2}</p> \n
            <p style="font-family:Courier; font-size: 20px;">{explanation_3}</p>
        """,
        unsafe_allow_html=True,
    )


st.header("Bring your own Pokemon")
st.write(
    "Enter your pokemon name and set its stats. Click 'Run Battle' to see how it performs"
)

with st.form(key="scenario_modeler"):
    option_set1, option_set2 = st.columns([4, 4])
    custom_pokemon_name = option_set1.text_input("custom_pokemon_name", "Brettasaurus")
    custom_pokemon_type1 = option_set1.selectbox("custom_pokemon_type", types)
    custom_pokemon_type2 = option_set1.selectbox(
        "custom_pokemon_type2", ["None"] + [i for i in types]
    )
    custom_pokemon_generation = option_set1.number_input(
        "Generation", min_value=1, value=7
    )
    custom_pokemon_legendary = option_set1.checkbox("Legendary", value=False)
    custom_pokemon_hp = option_set2.number_input(
        "HP", value=median_stats.get("hp"), step=1
    )
    custom_pokemon_speed = option_set2.number_input(
        "Speed", value=median_stats.get("speed"), step=1
    )
    custom_pokemon_attack = option_set2.number_input(
        "Attack", value=median_stats.get("attack"), step=1
    )
    custom_pokemon_defense = option_set2.number_input(
        "Defense", value=median_stats.get("defense"), step=1
    )
    custom_pokemon_sp_attack = option_set2.number_input(
        "Special Attack", value=median_stats.get("sp_attack"), step=1
    )
    custom_pokemon_sp_defense = option_set2.number_input(
        "Special Defense", value=median_stats.get("sp_defense"), step=1
    )

    pressed_scenario = st.form_submit_button("Run Scenario?")

prediction = st.empty()

if pressed_scenario > 0:
    logger.info("Battle On")
    custom_pokemon_dict = {
        "pokemon_1_name": [custom_pokemon_name],
        "pokemon_1_type_1": [custom_pokemon_type1],
        "pokemon_1_type_2": [custom_pokemon_type2],
        "pokemon_1_generation": [custom_pokemon_generation],
        "pokemon_1_legendary": [custom_pokemon_legendary],
        "pokemon_1_hp": [custom_pokemon_hp],
        "pokemon_1_speed": [custom_pokemon_speed],
        "pokemon_1_attack": [custom_pokemon_attack],
        "pokemon_1_defense": [custom_pokemon_defense],
        "pokemon_1_sp_attack": [custom_pokemon_sp_attack],
        "pokemon_1_sp_defense": [custom_pokemon_sp_defense],
    }
    prep_for_custom_battle = hf.process_for_custom_battle(
        pokemon, pokemon2, custom_pokemon_dict
    )

    battle_results, preds = hf.run_pokemon_battle(prep_for_custom_battle)

    winner = custom_pokemon_name if battle_results > 0.5 else pokemon2
    battle_loc.subheader(
        f"And the winner between {custom_pokemon_name} and {pokemon2} is: {winner}!"
    )
    try:
        battle_image.image(
            f"images/{winner}.png",
            width=150,
        )
    except Exception as e:
        logger.warning(e)

    explanation_1 = f"{preds['EXPLANATION_1_FEATURE_NAME'][0].replace('_', ' ').upper()} {preds['EXPLANATION_1_QUALITATIVE_STRENGTH'][0]}"
    explanation_2 = f"{preds['EXPLANATION_2_FEATURE_NAME'][0].replace('_', ' ').upper()} {preds['EXPLANATION_2_QUALITATIVE_STRENGTH'][0]}"
    explanation_3 = f"{preds['EXPLANATION_3_FEATURE_NAME'][0].replace('_', ' ').upper()} {preds['EXPLANATION_3_QUALITATIVE_STRENGTH'][0]}"
    battle_explanation.markdown(
        f"""
            <h3>Primary Drivers:</h3> \n
            <p style="font-family:Courier; font-size: 20px;">{explanation_1}</p> \n
            <p style="font-family:Courier; font-size: 20px;">{explanation_2}</p> \n
            <p style="font-family:Courier; font-size: 20px;">{explanation_3}</p>
        """,
        unsafe_allow_html=True,
    )
