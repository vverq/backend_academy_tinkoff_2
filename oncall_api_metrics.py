import logging
import random
import signal
import sys
import time
import httpx
from prometheus_client import start_http_server, Gauge, Counter
from environs import Env
from collections import defaultdict
import datetime


EXPORTER_API_REQUESTS_TOTAL = Counter(
    "exporter_api_requests_total", "Total count of requests to oncall API"
)
EXPORTER_API_REQUESTS_FAILED_TOTAL = Counter(
    "exporter_api_requests_failed_total", "Total count of failed requests to oncall API"
)
EXPORTER_API_LATENCY = Gauge(
    "exporter_api_latency", "Latency of requests to api oncall"
)
EXPORTER_TODAY_DUTY_TOTAL = Gauge(
    "exporter_today_duty_total", "Total count of duties today in a team", ["team"]
)
DOWNTIME = Gauge(
    "downtime", "The difference in seconds between two unsuccessful probes"
)

env = Env()


class Config:
    oncall_exporter_api_url = env("ONCALL_EXPORTER_API_URL", "http://oncall/api/v0")
    oncall_exporter_scrape_interval = env.int("ONCALL_EXPORTER_SCRAPE_INTERVAL", 15)
    oncall_exporter_log_level = env.log_level("ONCALL_EXPORTER_LOG_LEVEL", logging.INFO)
    oncall_exporter_metrics_port = env.int("ONCALL_EXPORTER_METRICS_PORT", 9099)

class OncallClient:
    def __init__(self, config):
        self.oncall_api_url = config.oncall_exporter_api_url
        self.previous_probe_is_successful = True
        self.previous_probe_time = None


    def populate(self):
        logging.debug("Sending request to oncall api")
        probe_is_successful = True
        with httpx.Client() as client:
            date = int(time.mktime(datetime.datetime.today().timetuple()))
            probe_time = datetime.datetime.utcnow()
            try:
                response = client.get(f"http://oncall-web:8080/api/v0/events?start__lt={date}&end__gt={date}")
            except Exception as e:
                probe_is_successful = False
                EXPORTER_API_REQUESTS_FAILED_TOTAL.inc()
            else:
                EXPORTER_API_REQUESTS_TOTAL.inc()
                if response.status_code != 200:
                    EXPORTER_API_REQUESTS_FAILED_TOTAL.inc()
                    probe_is_successful = False
                response_duration = response.elapsed.total_seconds()
                EXPORTER_API_LATENCY.set(response_duration)
                if response_duration > 0.05:
                    probe_is_successful = False
                response = response.json()
                duties_in_teams = defaultdict(int)
                for event in response:
                    team = event["team"]
                    duties_in_teams[team] += 1
                if len(duties_in_teams.items()) == 0:
                    probe_is_successful = False
                else:
                    for team, count in duties_in_teams.items():
                        if count == 0:
                            probe_is_successful = False
                        EXPORTER_TODAY_DUTY_TOTAL.labels(team=team).set(count)
            if not probe_is_successful:
                if self.previous_probe_time:
                    DOWNTIME.set((probe_time - self.previous_probe_time).total_seconds())
                self.previous_probe_time = probe_time
                self.previous_probe_is_successful = False
            else:
                self.previous_probe_time = None
                self.previous_probe_is_successful = True


def setup_logging(config):
    logging.basicConfig(
        stream=sys.stdout,
        level=config.oncall_exporter_log_level,
        format="%(asctime)s %(levelname)s:%(message)s"
    )


def main():
    config = Config()
    setup_logging(config)
    logging.info(f"Starting exporter on port {config.oncall_exporter_metrics_port}")
    start_http_server(config.oncall_exporter_metrics_port)
    client = OncallClient(config)
    while True:
        logging.debug("Populate from oncall")
        client.populate()
        logging.debug(f"Waiting {config.oncall_exporter_scrape_interval} seconds for next loop")
        time.sleep(config.oncall_exporter_scrape_interval)


def terminate(signal, frame):
    sys.exit(0)


if __name__=="__main__":
    signal.signal(signal.SIGTERM, terminate)
    main()
