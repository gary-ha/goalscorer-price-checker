from fuzzywuzzy import fuzz
import datetime
import pandas as pd
from google_sheets_api import GoogleSheetsAPI


class CalculateOutliers(GoogleSheetsAPI):
    def __init__(self):
        super().__init__()
        self.outlier_goalscorers = []
        self.inactive_participants = []
        self.duplicates = []
        self.change_weightings = []
        self.FULL_NAME = "Full Name"
        self.BETRADAR_ID = "Betradar ID"
        self.PARTICIPANT_ID = "Participant ID"
        self.PLAYER = "Player"
        self.METRIC_FGS = "Metric FGS"
        self.BETRADAR_FGS = "Betradar FGS"
        self.EVENT_ID = "Event ID"
        self.NOTES = "Notes"

    def calculate_outliers(self, goalscorer_data, br_goalscorers):
        print("Calculating outliers...")
        for metric_player in goalscorer_data:
            if float(metric_player["FGS"]) != 0:
                for betradar_player in br_goalscorers:
                    if fuzz.ratio(metric_player[self.FULL_NAME], betradar_player[self.PLAYER]) > 90 and \
                            int(metric_player[self.BETRADAR_ID]) == int(betradar_player[self.BETRADAR_ID]):
                        self.check_inactive(metric_player, betradar_player)
                        break

    def check_inactive(self, metric_player, betradar_player):
        if betradar_player["FGS"] != "-.-":
            metric_odds = float(metric_player["FGS"])
            betradar_odds = float(betradar_player["FGS"])
            prob_metric = 1 / metric_odds
            prob_betradar = 1 / betradar_odds
            if prob_betradar - prob_metric > 0.04 or prob_metric - prob_betradar > 0.06:
                self.outlier_goalscorers.append({
                    self.PARTICIPANT_ID: f"{metric_player[self.PARTICIPANT_ID]};",
                    self.PLAYER: metric_player[self.FULL_NAME],
                    self.METRIC_FGS: metric_odds,
                    self.BETRADAR_FGS: betradar_odds,
                    self.BETRADAR_ID: metric_player[self.BETRADAR_ID],
                    self.EVENT_ID: metric_player[self.EVENT_ID],
                    self.NOTES: ""
                })
        else:
            self.inactive_participants.append({
                self.PARTICIPANT_ID: f"{metric_player[self.PARTICIPANT_ID]};",
                self.PLAYER: metric_player[self.FULL_NAME],
                self.METRIC_FGS: float(metric_player["FGS"]),
                self.BETRADAR_FGS: "No Price",
                self.BETRADAR_ID: metric_player[self.BETRADAR_ID],
                self.EVENT_ID: metric_player[self.EVENT_ID],
                self.NOTES: "Possible Injury/Non Team Selection"
            })

    def find_duplicates(self, goalscorer_data):
        print("Find possible duplicates...")
        for player_index in range(len(goalscorer_data)):
            for next_player_index in goalscorer_data[player_index+1:]:
                if fuzz.ratio(goalscorer_data[player_index][self.FULL_NAME], next_player_index[self.FULL_NAME]) > 90 and \
                        int(goalscorer_data[player_index][self.BETRADAR_ID]) == int(next_player_index[self.BETRADAR_ID]):
                    self.duplicates.append({
                        "Date": f"{datetime.datetime.now().strftime('%d/%m/%Y')}",
                        self.PARTICIPANT_ID: f"{goalscorer_data[player_index][self.PARTICIPANT_ID]};",
                        self.PLAYER: goalscorer_data[player_index][self.FULL_NAME],
                        self.METRIC_FGS: float(goalscorer_data[player_index]["FGS"]),
                        self.BETRADAR_FGS: "",
                        self.BETRADAR_ID: goalscorer_data[player_index][self.BETRADAR_ID],
                        self.EVENT_ID: goalscorer_data[player_index][self.EVENT_ID],
                        self.NOTES: "Possible Duplicate, please check."
                    })
                    break

    def calculate_new_waiting(self, ftts_prices):
        print("Calculating new goalweights...")
        data = self.pull_participants_data()
        df = pd.DataFrame(data[1:], columns=data[0])
        participant_information = df.to_dict("records")
        for player in self.outlier_goalscorers:
            self.check_if_in_participant_csv(player, participant_information, ftts_prices)

    def check_if_in_participant_csv(self, player, participant_information, ftts_prices):
        for player_info in participant_information:
            if player[self.PARTICIPANT_ID] == player_info["Id"]:
                self.find_team_info(player, player_info, ftts_prices)
                break

    def find_team_info(self, player, player_info, ftts_prices):
        temp_team_club_id = player_info["Team1"]
        temp_team_country_id = player_info["Team2"]
        ftts_price = 0
        for price in ftts_prices:
            if price[self.EVENT_ID] == player[self.EVENT_ID]:
                if price["Home Team"] == temp_team_club_id:
                    ftts_price = float(price["Home"])
                if price["Home Team"] == temp_team_country_id:
                    ftts_price = float(price["Home"])
                if price["Away Team"] == temp_team_club_id:
                    ftts_price = float(price["Away"])
                if price["Away Team"] == temp_team_country_id:
                    ftts_price = float(price["Away"])
                break
        self.find_new_weighting(player, ftts_price)

    def find_new_weighting(self, player, ftts_price):
        if ftts_price != 0:
            new_weighting = (1 / player[self.BETRADAR_FGS]) / (1 / ftts_price)
            if player[self.METRIC_FGS] > player[self.BETRADAR_FGS]:
                self.change_weightings.append({
                    "Date": f"{datetime.datetime.now().strftime('%d/%m/%Y')}",
                    self.PARTICIPANT_ID: player['Participant ID'],
                    self.PLAYER: player[self.PLAYER],
                    "Metric 100% FGS": float(player[self.METRIC_FGS]),
                    "Betradar 100% FGS": float(player[self.BETRADAR_FGS]),
                    self.BETRADAR_ID: player[self.BETRADAR_ID],
                    self.EVENT_ID: player[self.EVENT_ID],
                    "New Weighting": round(new_weighting, 3),
                    "Status": "Changed"
                })
            if player[self.METRIC_FGS] < player[self.BETRADAR_FGS]:
                self.change_weightings.append({
                    "Date": f"{datetime.datetime.now().strftime('%d/%m/%Y')}",
                    self.PARTICIPANT_ID: player[self.PARTICIPANT_ID],
                    self.PLAYER: player[self.PLAYER],
                    "Metric 100% FGS": float(player[self.METRIC_FGS]),
                    "Betradar 100% FGS": float(player[self.BETRADAR_FGS]),
                    self.BETRADAR_ID: player[self.BETRADAR_ID],
                    self.EVENT_ID: player[self.EVENT_ID],
                    "New Weighting": round(new_weighting, 3),
                    "Status": "Please Check Proposed Weighting"
                })
