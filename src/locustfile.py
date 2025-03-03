from locust import events, task, FastHttpUser
import random
import logging

logger = logging.getLogger(__name__)


@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument("--log-file", type=str, env_var="LOG_FILE", default="default.log", help="Log file name")
    parser.add_argument("--log-level", type=str, env_var="LOG_LEVEL", default="WARNING", help="Log level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    parser.add_argument("--tasks", type=str, env_var="TASKS", default="get_collections", help="Comma-separated list of tasks to run")
    parser.add_argument("--url", type=str, env_var="URL", default="https://oaktrust-pre.library.tamu.edu", help="Base URL")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    try:
        log_file = environment.parsed_options.log_file
        log_level = environment.parsed_options.log_level

        logging_levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }

        logging_level = logging_levels.get(log_level, logging.WARNING)

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        logging.basicConfig(
            filename=log_file,
            filemode='a',
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            level=logging_level
        )

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging_level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    except Exception as error:
        print(error)
        environment.runner.quit()


@events.request.add_listener
def log_request(request_type, name, response_time, response_length, response, context, exception, start_time, url,
                **kwargs):
    try:
        if exception:
            logger.error(f"FAILURE: {request_type} {name} {response_time} {exception} at {start_time} for {url}")
        elif response_time > 20000:
            logger.warning(f"Long Request: {name} took {response_time} for {url} at {start_time}")
        elif response_time > 1000:
            logger.warning(f"At least a second: {name} took {response_time} for {url} at {start_time}")
        else:
            logger.info(f"Request: {request_type} {name} {response_time} for {url}.")
    except Exception as e:
        print(f"Logging error: {e} for {url}")


class OakTrustTester(FastHttpUser):
    host = "https://oaktrust-pre.library.tamu.edu"
    tasks = []

    @task
    def get_collections(self):
        response = self.client.get(f"{self.host}/server/api/core/collections", name="Get Collection Data from API")
        page_data = response.json().get('page')
        total_elements = page_data.get('totalElements')
        current = random.randint(0, total_elements - 1)
        current_collections = self.client.get(f"{self.host}/server/api/core/collections?page={current}size=1", name="Get Random List of Collections from API").json().get("_embedded").get('collections')
        for collection in current_collections:
            uuid = collection.get('uuid')
            self.client.get(f"{self.host}/collections/{uuid}", name="Get Collection by UUID")
        return

    @task
    def lookup_authors(self):
        current = random.randint(0, 300)
        response = self.client.get(
            f"{self.host}/server/api/discover/facets/author?page={current}",
            name="Get Authors Data from API"
        )
        authors = response.json().get('_embedded').get('values')
        rand_author = random.choice(authors)
        author_search = self.client.get(rand_author["_links"]["search"]["href"], name="Get Random Author Articles from API")
        for article in author_search.json()['_embedded']['searchResult']['_embedded']["objects"]:
            self.client.get(f"{self.host}/items/{article["_embedded"]["indexableObject"]["uuid"]}", name="Get Article by UUID")

    @task
    def download_bitstreams(self):
        current = random.randint(0, 300)
        response = self.client.get(
            f"{self.host}/server/api/discover/facets/author?page={current}",
            name="Get Authors Data from API"
        )
        authors = response.json().get('_embedded').get('values')
        rand_author = random.choice(authors)
        author_search = self.client.get(rand_author["_links"]["search"]["href"],
                                        name="Get Random Author Articles from API")
        all_article_response = author_search.json()["_embedded"]["searchResult"]['_embedded']['objects']
        all_articles = [item['_links']['indexableObject']['href'] for item in all_article_response]
        random_article = random.choice(all_articles)
        article_response = self.client.get(
            random_article,
            name="Get Article API Response by UUID"
        ).json()
        bundles = self.client.get(article_response.get('_links')['bundles']['href'], name="Get Bundle API Response")
        random_bundle = random.choice(bundles.json()['_embedded']['bundles'])
        random_bundle_response = self.client.get(
            f"{self.host}/server/api/core/bundles/{random_bundle['uuid']}/bitstreams",
            name="Get Random Bundle's Bitstreams"
        ).json()
        random_bitstream = random.choice(random_bundle_response['_embedded']['bitstreams'])
        self.client.get(f"{self.host}/bitstreams/{random_bitstream['uuid']}/download", name="Download Random Bitstream")


@events.init.add_listener
def _(environment, **kwargs):
    tasks_arg = environment.parsed_options.tasks
    if tasks_arg:
        tasks_to_run = tasks_arg.split(",")
    else:
        tasks_to_run = ["get_collections"]

    task_mapping = {
        "get_collections": OakTrustTester.get_collections,
        "lookup_authors": OakTrustTester.lookup_authors,
        "download_bitstreams": OakTrustTester.download_bitstreams
    }

    OakTrustTester.tasks = [task_mapping[task_name] for task_name in tasks_to_run]
