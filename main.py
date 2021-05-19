from metric_api import MetricAPI
from betradar_scraper import BetradarScraper
from google_sheets_api import GoogleSheetsAPI
from calculate_outliers import CalculateOutliers

metric_api = MetricAPI()
betradar_scraper = BetradarScraper()
calculate_outliers = CalculateOutliers()
google_sheets_api = GoogleSheetsAPI()

if __name__ == "__main__":
    metric_api.get_events_with_goalscorers()
    metric_api.get_metric_goalscorer_prices()
    betradar_scraper.scrape_br_goalscorers(metric_api.br_ids)
    calculate_outliers.calculate_outliers(metric_api.goalscorer_data, betradar_scraper.br_goalscorers)
    calculate_outliers.find_duplicates(metric_api.goalscorer_data)
    calculate_outliers.calculate_new_waiting(metric_api.ftts_prices)
    metric_api.change_participant_weightings(calculate_outliers.change_weightings)
    metric_api.untick_inactives(calculate_outliers.inactive_participants)
    google_sheets_api.export_to_google_sheet(calculate_outliers.change_weightings, calculate_outliers.duplicates)
