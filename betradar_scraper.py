from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from decouple import config
import time
import pandas as pd


class BetradarScraper:
    def __init__(self):
        self.br_goalscorers = []
        self.odds_list = []
        self.players_list = []
        self.betradar_url = "https://ctrl.betradar.com/monitoring"
        self.df = pd.DataFrame(columns=["Player", "FGS", "Betradar ID"])
        self.options = Options()
        self.options.add_argument("--headless")
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(options=self.options,
                                       executable_path=r'C:\Users\FiercePC\AppData\Local\Programs\Python\Python38\Scripts\chromedriver.exe')
        # self.driver = webdriver.Chrome(options=self.options)
        self.driver.create_options()

    def scrape_br_goalscorers(self, br_ids):
        print("Loading up Selenium Browser...")
        self.driver.get(self.betradar_url)
        print("Loaded up Selenium Browser...")
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//*[@id='username']")))
        username = self.driver.find_element_by_xpath("//*[@id='username']")
        username.send_keys(config('BR_USERNAME'))
        password = self.driver.find_element_by_xpath("//*[@id='password']")
        password.send_keys(config('BR_PASSWORD'))
        sign_in = self.driver.find_element_by_xpath("//*[@id='loginForm']/button")
        sign_in.click()
        time.sleep(5)
        self.scrape_odds(br_ids)
        self.br_goalscorers_to_dict()
        self.driver.close()

    def scrape_odds(self, br_ids):
        for br_id in br_ids:
            self.odds_list = []
            self.players_list = []
            temp_list = []
            betradar_url_match = f"https://ctrl.betradar.com/match/sr:match:{br_id}/market-groups/7e7ec0dcf98f4deb/101?ownOdds=1"
            self.driver.get(betradar_url_match)
            time.sleep(1)
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "own-odds-section")))
                odds = self.driver.find_elements_by_class_name("own-odds-section")
                for o in odds:
                    odds1 = o.find_elements_by_class_name("match-odds-cell")
                    for o1 in range(len(odds1)):
                        temp_list.append(odds1[o1].text)

                if self.have_odds(temp_list):
                    self.scrape_name()

                self.consolidate(br_id)

            except NoSuchElementException:
                continue

    def have_odds(self, temp_list):
        have_odds = False
        for t in temp_list:
            if t != "-.-":
                have_odds = True
                break
        if have_odds:
            for y in temp_list:
                self.odds_list.append(y)
            return True

    def scrape_name(self):
        players = self.driver.find_elements_by_class_name("outcome-name-text")
        for p in range(len(players)):
            self.players_list.append(players[p].text)
        for index in range(len(self.players_list)):
            if "," in self.players_list[index]:
                a, b = self.players_list[index].split(',')
                b = b.strip()
                self.players_list[index] = f"{b} {a}"

    def consolidate(self, br_id):
        data_tuples = list(zip(self.players_list[3:], self.odds_list[3:]))
        temp_df = pd.DataFrame(data_tuples, columns=["Player", "FGS"])
        temp_df["Betradar ID"] = br_id
        self.df = self.df.append(temp_df)

    def br_goalscorers_to_dict(self):
        self.br_goalscorers = self.df.to_dict("records")
        print(self.br_goalscorers)
