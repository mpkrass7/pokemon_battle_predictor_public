"""
Usage:
    python datarobot-predict.py <input-file.csv>

This example uses the requests library which you can install with:
    pip install requests
We highly recommend that you update SSL certificates with:
    pip install -U urllib3[secure] certifi
"""
import sys
import json
import requests

import pandas as pd
import streamlit as st

DEPLOYMENT_ID = st.secrets["DEPLOYMENT_ID"]
API_URL = f"https://cfds-ccm-prod.orm.datarobot.com/predApi/v1.0/deployments/{DEPLOYMENT_ID}/predictions"  # noqa
API_KEY = st.secrets["API_KEY"]
DATAROBOT_KEY = st.secrets["DATAROBOT_KEY"]

# Don't change this. It is enforced server-side too.
MAX_PREDICTION_FILE_SIZE_BYTES = 52428800  # 50 MB


class DataRobotPredictionError(Exception):
    """Raised if there are issues getting predictions from DataRobot"""


def make_datarobot_deployment_predictions(data, deployment_id):
    """
    Make predictions on data provided using DataRobot deployment_id provided.
    See docs for details:
         https://app.datarobot.com/docs/predictions/api/dr-predapi.html

    Parameters
    ----------
    data : str
        If using CSV as input:
        Feature1,Feature2
        numeric_value,string

        Or if using JSON as input:
        [{"Feature1":numeric_value,"Feature2":"string"}]

    deployment_id : str
        The ID of the deployment to make predictions with.

    Returns
    -------
    Response schema:
        https://app.datarobot.com/docs/predictions/api/dr-predapi.html#response-schema

    Raises
    ------
    DataRobotPredictionError if there are issues getting predictions from DataRobot
    """
    # Set HTTP headers. The charset should match the contents of the file.
    headers = {
        # As default, we expect CSV as input data.
        # Should you wish to supply JSON instead,
        # comment out the line below and use the line after that instead:
        "Content-Type": "text/plain; charset=UTF-8",
        # 'Content-Type': 'application/json; charset=UTF-8',
        "Authorization": "Bearer {}".format(API_KEY),
        "DataRobot-Key": DATAROBOT_KEY,
    }

    url = API_URL

    # Prediction Explanations:
    # See the documentation for more information:
    # https://app.datarobot.com/docs/predictions/api/dr-predapi.html#request-pred-explanations
    # Should you wish to include Prediction Explanations or Prediction Warnings in the result,
    # Change the parameters below accordingly, and remove the comment from the params field below:

    params = {
        # If explanations are required, uncomment the line below
        # "minExplanations": 3,
        "maxExplanations": 3,
        "thresholdHigh": 0.5,
        "thresholdLow": 0.15,
        # Uncomment this for Prediction Warnings, if enabled for your deployment.
        # 'predictionWarningEnabled': 'true',
    }
    # Make API request for predictions
    predictions_response = requests.post(
        url,
        data=data,
        headers=headers,
        # Prediction Explanations:
        # Uncomment this to include explanations in your prediction
        params=params,
    )
    _raise_dataroboterror_for_status(predictions_response)
    # Return a Python dict following the schema in the documentation
    return predictions_response.json()


def _raise_dataroboterror_for_status(response):
    """Raise DataRobotPredictionError if the request fails along with the response returned"""
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        err_msg = "{code} Error: {msg}".format(
            code=response.status_code, msg=response.text
        )
        raise DataRobotPredictionError(err_msg)


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
            exp0, exp1, exp2 = {"feature":""}, {"feature":""}, {"feature":""}
        elif len(explanations) >= 3:
            exp0, exp1, exp2 = explanations[0], explanations[1], explanations[2]
        elif len(explanations) == 2:
            exp0, exp1, exp2 = explanations[0], explanations[1], {"feature":""}
        elif len(explanations) == 1:
            exp0, exp1, exp2 = explanations[0], {"feature":""}, {"feature":""}
        else:
            exp0, exp1, exp2 = {"feature":""}, {"feature":""}, {"feature":""}

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


def main(filename, deployment_id):
    """
    Return an exit code on script completion or error. Codes > 0 are errors to the shell.
    Also useful as a usage demonstration of
    `make_datarobot_deployment_predictions(data, deployment_id)`
    """
    if not filename:
        print(
            "Input file is required argument. "
            "Usage: python datarobot-predict.py <input-file.csv>"
        )
        return 1
    data = open(filename, "rb").read()
    data_size = sys.getsizeof(data)
    if data_size >= MAX_PREDICTION_FILE_SIZE_BYTES:
        print(
            (
                "Input file is too large: {} bytes. " "Max allowed size is: {} bytes."
            ).format(data_size, MAX_PREDICTION_FILE_SIZE_BYTES)
        )
        return 2
    try:
        predictions = make_datarobot_deployment_predictions(data, deployment_id)
    except DataRobotPredictionError as exc:
        print(exc)
        return exc
    return dataframify_predictions(preds=predictions)


if __name__ == "__main__":
    filename = sys.argv[1]
    sys.exit(main(filename, DEPLOYMENT_ID))
