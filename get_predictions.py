"""
Usage:
    python datarobot-predict.py <input-file.csv>

This example uses the requests library which you can install with:
    pip install requests
We highly recommend that you update SSL certificates with:
    pip install -U urllib3[secure] certifi
"""

import pandas as pd
from datarobot_predict.scoring_code import ScoringCodeModel


MODEL = ScoringCodeModel("model.jar")


def dataframify_predictions(preds):
    """
    Converts Prediction Response from DataRobot API into a Pandas Dataframe. Works fast enough for my demo purposes
    preds: list of dictionaries returned by DataRobot API

    """
    predictions = preds["data"]
    rowId = []
    predictionValue = []

    explanation_0_feature = []
    explanation_0_feature_value = []
    explanation_0_qualitative_strength = []
    explanation_0_strength = []

    explanation_1_feature = []
    explanation_1_feature_value = []
    explanation_1_qualitative_strength = []
    explanation_1_strength = []

    explanation_2_feature = []
    explanation_2_feature_value = []
    explanation_2_qualitative_strength = []
    explanation_2_strength = []

    for row in predictions:
        rowId.append(row.get("rowId"))
        predictionValue.append(row.get("predictionValues")[0].get("value"))
        explanations = row.get("predictionExplanations")
        if not explanations:
            exp0, exp1, exp2 = {"feature": ""}, {"feature": ""}, {"feature": ""}
        elif len(explanations) >= 3:
            exp0, exp1, exp2 = explanations[0], explanations[1], explanations[2]
        elif len(explanations) == 2:
            exp0, exp1, exp2 = explanations[0], explanations[1], {"feature": ""}
        elif len(explanations) == 1:
            exp0, exp1, exp2 = explanations[0], {"feature": ""}, {"feature": ""}
        else:
            exp0, exp1, exp2 = {"feature": ""}, {"feature": ""}, {"feature": ""}

        explanation_0_feature.append(exp0.get("feature"))
        explanation_0_feature_value.append(str(exp0.get("featureValue")))
        explanation_0_qualitative_strength.append(exp0.get("qualitativeStrength"))
        explanation_0_strength.append(exp0.get("strength"))

        explanation_1_feature.append(exp1.get("feature"))
        explanation_1_feature_value.append(str(exp1.get("featureValue")))
        explanation_1_qualitative_strength.append(exp1.get("qualitativeStrength"))
        explanation_1_strength.append(exp1.get("strength"))

        explanation_2_feature.append(exp2.get("feature"))
        explanation_2_feature_value.append(str(exp2.get("featureValue")))
        explanation_2_qualitative_strength.append(exp2.get("qualitativeStrength"))
        explanation_2_strength.append(exp2.get(str("strength")))

    prediction_data = pd.DataFrame(
        {
            "rowId": rowId,
            "predictionValue": predictionValue,
            "explanation_0_feature": explanation_0_feature,
            "explanation_0_feature_value": explanation_0_feature_value,
            "explanation_0_qualitative_strength": explanation_0_qualitative_strength,
            "explanation_0_strength": explanation_0_strength,
            "explanation_1_feature": explanation_1_feature,
            "explanation_1_feature_value": explanation_1_feature_value,
            "explanation_1_qualitative_strength": explanation_1_qualitative_strength,
            "explanation_1_strength": explanation_1_strength,
            "explanation_2_feature": explanation_2_feature,
            "explanation_2_feature_value": explanation_2_feature_value,
            "explanation_2_qualitative_strength": explanation_2_qualitative_strength,
            "explanation_2_strength": explanation_2_strength,
        },
    )
    return prediction_data


def main(data: pd.DataFrame) -> pd.DataFrame:
    """
    Return an exit code on script completion or error. Codes > 0 are errors to the shell.
    Also useful as a usage demonstration of
    `make_datarobot_deployment_predictions(data, deployment_id)`
    """
    return MODEL.predict(data, max_explanations=3)
