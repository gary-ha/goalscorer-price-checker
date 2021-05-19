import requests
from decouple import config
import datetime


class MetricAPI:
    def __init__(self):
        self.category_ids = config('CATEGORY_ID').split(",")
        self.metric_ids = []
        self.br_ids = []
        self.goalscorer_data = []
        self.ftts_prices = []
        self.gameweb = config('GAME_WEB')
        self.betpumpweb = config('BETPUMPWEB')

    def get_events_with_goalscorers(self):
        print(datetime.datetime.now())
        print("Gathering events with Goalscorers...")
        for category in self.category_ids:
            try:
                parameters = {
                    "fn": "events",
                    "org": "snabbis",
                    "lang": "en",
                    "categoryid": f"{category}",
                    "status": "Live"
                }
                response = requests.get(url=self.gameweb, params=parameters)
                response.raise_for_status()
                events_data = response.json()
                for event in events_data["data"]:
                    if event["scorers"] and event["state"]["periodId"] == "PreGame":
                        time_delta = datetime.datetime.strptime(event["startTime"], "%Y-%m-%d %H:%M:%S") - (
                                    datetime.datetime.now() - datetime.timedelta(hours=1))
                        difference_minutes = int(time_delta.total_seconds() / 60)
                        if difference_minutes > 90:
                            self.metric_ids.append(event["id"])
            except KeyError:
                continue
        print(self.metric_ids)

    def get_metric_goalscorer_prices(self):
        print("Gathering Metric Goalscorer prices...")
        for event in self.metric_ids:
            parameters = {
                "fn": "event",
                "org": "Operator B",
                "lang": "en",
                "eventid": event,
                "markets": "Yes",
                "selections": "Yes",
                "marketstatus": "Open",
            }

            response = requests.get(url=self.gameweb, params=parameters)
            response.raise_for_status()
            event_data = response.json()

            if event_data["data"]["scorers"]:
                format_goalscorer = []
                self.br_ids.append(int(event_data["data"]["xids"]["betradarId"]))

                for market in event_data["data"]["markets"]:
                    if market["name"] == "Next Goalscorer":
                        for player in market["selections"]:
                            format_goalscorer.append({"Participant ID": player["participantId"],
                                                      "Full Name": "",
                                                      "FGS": player["odds"],
                                                      "Betradar ID": event_data["data"]["xids"]["betradarId"],
                                                      "Event ID": f"{event};"})

                self.get_ftts_prices(event, event_data)
                self.get_full_names(event_data, format_goalscorer)

        print(self.br_ids)

    def get_ftts_prices(self, event, event_data):
        for market in event_data["data"]["markets"]:
            if market["name"] == "Team To Score First" or market["name"] == "First Team to Score":
                self.ftts_prices.append({
                    "Event ID": f"{event};",
                    "Home Team": f"{event_data['data']['participants'][0]['id']};",
                    "Away Team": f"{event_data['data']['participants'][1]['id']};",
                    market["selections"][0]["idName"]: market["selections"][0]["odds"],
                    market["selections"][1]["idName"]: market["selections"][1]["odds"],
                    market["selections"][2]["idName"]: market["selections"][2]["odds"],
                })

    def get_full_names(self, event_data, format_goalscorer):
        for player_dict in format_goalscorer:
            for participant in event_data["data"]["participants"]:
                if player_dict["Participant ID"] == participant["id"]:
                    player_dict["Full Name"] = participant["name"]
                    self.goalscorer_data.append(player_dict)
                    break

    def change_participant_weightings(self, change_weightings):
        parameters = {
            "fn": "loginadmin",
            "org": "BetPump",
            "uid": config('BO_USERNAME'),
            "pwd": config('BO_PASSWORD'),
        }

        response = requests.get(url=self.betpumpweb, params=parameters)
        response.raise_for_status()
        session_id = response.json()["data"]["session"]

        print("Changing Participant Weightings...")
        for player in change_weightings:
            if player["Status"] == "Changed":

                parameters = {
                    "fn": "seteventparticipantproperty",
                    "org": "BetPump",
                    "lang": "EN",
                    "eventid": player["Event ID"].split(";")[0],
                    "participantids": player["Participant ID"].split(";")[0],
                    "prop": "goalweight",
                    "val": player["New Weighting"],
                    "sessid": session_id,
                }

                response = requests.post(url=self.betpumpweb, params=parameters)
                response.raise_for_status()

    def untick_inactives(self, inactive_participants):
        parameters = {
            "fn": "loginadmin",
            "org": "BetPump",
            "uid": config('BO_USERNAME'),
            "pwd": config('BO_PASSWORD'),
        }

        response = requests.get(url=self.betpumpweb, params=parameters)
        response.raise_for_status()
        session_id = response.json()["data"]["session"]

        print("Unticking Inactives...")
        for player in inactive_participants:

            parameters = {
                "fn": "seteventparticipantproperty",
                "org": "BetPump",
                "lang": "EN",
                "eventid": player["Event ID"].split(";")[0],
                "participantids": player["Participant ID"].split(";")[0],
                "prop": "participate",
                "val": "No",
                "sessid": session_id,
            }

            response = requests.post(url=self.betpumpweb, params=parameters)
            response.raise_for_status()
