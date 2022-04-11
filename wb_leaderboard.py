#!/usr/bin/env python3
#This is a module meant to be imported
import binascii
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from urllib.parse import quote
import base64
import requests
from requests import Request, Session
import json
import pandas as pd

# @input: track_id
# @output: leaderboard results in pandas dataframe
def get_leaderboard(track_id):
    #key
    key = 'BatCaveGGevaCtaB'
    key = key.encode('utf-8')
    cipher = AES.new(key, AES.MODE_ECB)
    payload = "track_id={}&sim_version=1.16&offset=0&count=200&protected_track_value=2&race_mode=6".format(track_id)
    payload = payload.encode('utf-8')
    #Encrypt the payload string
    msg_en = cipher.encrypt(pad(payload,16))
    #base64 encode the encrypted string
    output = quote(base64.b64encode(msg_en),safe='')
    #add prefix to encrypted string
    payload = "post_data={}".format(str(output))
    url = 'http://www.velocidrone.com/api/leaderboard/getLeaderBoard'
    headers = {
    'User-Agent': 'UnityPlayer/2020.3.8f1 (UnityWebRequest/1.0, libcurl/7.52.0-DEV)',
    'Accept': '*/*',
    'Accept-Encoding': 'identity',
    'Connection': 'Keep-Alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'X-Unity-Version': '2020.3.8f1',
    }
    #make api call
    s = Session()
    req = Request('POST', url, data=payload, headers=headers)
    prepped = req.prepare()
    response = s.send(prepped)
    #base64 decode and then decrypt the response
    decipher = AES.new(key, AES.MODE_ECB)
    result = decipher.decrypt(base64.b64decode(response.text))
    result = unpad(result, 16)
    #decode decrypted response
    result = result.decode('utf-8').strip()
    #convert to json object
    final = json.loads(result)
    if len(final['tracktimes'] == 0):
      print('Invalid track_id')
      quit(1)
    final_df = pd.json_normalize(final, record_path =['tracktimes'])
    final_df = final_df[['playername', 'lap_time']]
    final_df['lap_time'] = pd.to_numeric(final_df['lap_time'])
    final_df = final_df.rename({'playername': 'Player Name', 'lap_time': 'Lap Time'}, axis='columns')
    return(final_df.set_index('Player Name'))


