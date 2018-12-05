import pandas as pd 
import helper as hp 
from telemetry import TeleProcessor
    
def fetch(match_id):

    match_data = hp.getMatch('kakao', match_id)
    
    match_info = hp.processMatchData(match_data)
    map_name = match_info['mapName']
    game_mode = match_info['gameMode']

    url = hp.processTelemetryURL(match_data)
    tele_data = hp.getTelemetry(url)
    if game_mode == 'solo' and map_name=='Savage_Main':
        try:
            tele = TeleProcessor(teleData=tele_data)
            kills = tele.getKillsXY()
            df = pd.DataFrame(kills)
        except:
            df = pd.DataFrame()
    else:
        df = pd.DataFrame()

    return df
