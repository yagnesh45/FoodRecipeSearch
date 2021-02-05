# import packages
from flask import Flask, request, render_template
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import requests
import logging

app = Flask(__name__)

# setting up logging file
logging.basicConfig(
    filename="recipe.log",
    format="%(asctime)s %(levelname)s %(threadName)s %(name)s %(message)s",
    level=logging.INFO,
)

# setting the REST APIs and display file for search results.
SEARCH_RECIPE_TEMPLATE = "search-results.html"
BASE_URL = "https://api.edamam.com/search?"
APP_ID = "216ee2e1"
APP_KEY = "47753d7f0fef48214adaf64875cbb2f3"


# decorator for home page
@app.route("/")
def index():
    """Method for mapping of index.html page."""

    logging.info("On index page")

    return render_template("index.html")


def set_retry_policy():
    """Sets the retry Policy for request methods of API calls.
    
    returns: \\
        Session object of requests created by configuration 
        of retry strategies.
    """

    logging.info("Setting up the retry policy")

    retry_strategy = Retry(
        total=3,  # no of retries
        backoff_factor=1,  # time between retries
        status_forcelist=[429, 500, 502, 503, 504]
        # response codes to retry on
    )

    # logging every process of API calls
    logging.info("Setting the adapter with our retry strategy")
    adapter = HTTPAdapter(max_retries=retry_strategy)

    logging.info("Setting up the request session")
    http = requests.Session()

    logging.info("Mouting the base url")
    http.mount(BASE_URL, adapter)

    return http


def adjust_payload(food_dish, health_labels, diet_label, calories):
    """Setting up the payload to be sent via APIs.
    
    arguments: \\
        food_dish: name of the dish
        health_labels: selected checkbox items for health
        diet labels: selected radio button item for diet plan
        calories: maximum calories of recipe (By default 100g serving)

    returns: \\
        payload: Filtered and selected payload.
    """

    payload = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "q": food_dish,
        "healt": health_labels,
        "diet": diet_label,
        "calories": calories,
    }

    # cleaning out empty labels and other options
    # for advanced search
    if not health_labels:
        payload.pop("healt")

    if not diet_label:
        payload.pop("diet")

    if not calories:
        payload.pop("calories")

    return payload


@app.route("/search-recipe", methods=["GET", "POST"])
def search_recipe():
    """Method for mapping with search-results.html file """

    logging.info("On get recipe page")

    detail_of_dish = []

    if request.method == "GET":

        food_dish = request.args.get("recipe_search_query")
        health_labels = request.args.getlist("health-checkbox")
        diet_label = request.args.getlist("diet-checkbox")
        calories = request.args.get("kcal-input")

        # filtering and adjusting payload function call
        payload = adjust_payload(
            food_dish, health_labels, diet_label, calories
        )

        # Exception handling: for connection Timeout, TooManyRedirects,
        # & ReqeustsException
        try:
            http = set_retry_policy()
            response = http.get(BASE_URL, params=payload)

            logging.info("Calling URL {}".format(response.url))
            logging.info("Response Code {}".format(response.status_code))

            response = response.json()  # json format of response object

            if "more" in response and response["more"] == True:
                logging.info("Started fetching of data from response")

                # storing all the fetchedd information according to search
                # query and options
                for hits in response["hits"]:

                    dish = hits["recipe"]["label"]
                    ingredients = hits["recipe"]["ingredientLines"]
                    url = hits["recipe"]["url"]
                    image = hits["recipe"]["image"]
                    detail_of_dish.append([dish, ingredients, url, image])

                logging.info("Fetched required data from response")
            else:
                return render_template(SEARCH_RECIPE_TEMPLATE, more=False)

        except requests.exceptions.Timeout:  # storing exceptions in log file
            logging.error("Time out error occured")
        except requests.exceptions.TooManyRedirects:
            logging.error("Too many redirects")
        except requests.exceptions.RequestException as e:
            logging.error("Request Exception {}".format(e))

    return render_template(
        SEARCH_RECIPE_TEMPLATE, detail_of_dish=detail_of_dish, more=True
    )


# running the Flask application
if __name__ == "__main__":
    app.run(debug=True)
