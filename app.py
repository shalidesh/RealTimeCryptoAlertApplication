from flask import Flask,render_template, url_for, request,flash,redirect,Response,send_from_directory
from transformers import PegasusTokenizer, PegasusForConditionalGeneration  #Deep learning NLP Architectures
from bs4 import BeautifulSoup #work with html and web scrapping
import requests
from transformers import T5Tokenizer, T5ForConditionalGeneration
from transformers import PegasusForConditionalGeneration, AutoTokenizer

import websocket, json, pprint, talib, numpy
from binance.client import Client
from binance.enums import *
from threading import Thread
from notifypy import Notify  
from multiprocessing import Process, freeze_support
import pandas as pd

import chardet
import json

# specify path to save the model and tokenizer
path = './models/t5-small/'

tokenizer = T5Tokenizer.from_pretrained(path)
model = T5ForConditionalGeneration.from_pretrained(path)

app = Flask(__name__)

summery_path='./data/assetsummaries.csv'
monitored_tickers=[]
SOCKET = "wss://stream.binance.com:9443/stream?streams=ethusdt@kline_1m/btcusdt@kline_1m"

RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

ethcloses = []
btccloses = []


def rsiAlert(data,ticker):
     candle = data['k']
     is_candle_closed = candle['x']
     close = candle['c']

     if is_candle_closed:
          print("{} candle closed at {}".format(ticker,close))

          if ticker=="ETH-USD":
              ethcloses.append(float(close))
              print("closes")
              print(ethcloses)
              if len(ethcloses) > RSI_PERIOD:
                    
                    np_closes = numpy.array(ethcloses)
                    rsi = talib.RSI(np_closes, RSI_PERIOD)
                    print("all rsis calculated so far")
                    print(rsi)
                    last_rsi = rsi[-1]
                    print("the current rsi is {}".format(last_rsi))

                    if last_rsi > RSI_OVERBOUGHT:
                         
                         print("Overbought! Sell! Sell! Sell!")
                         msg=f"{ticker} are Overbought! Sell! Sell! Sell!"
                         alertSend(msg)
                         
                    if last_rsi < RSI_OVERSOLD:
                         print("Oversold! Buy! Buy! Buy!")
                         msg=f"{ticker} Oversold! Buy! Buy! Buy!"
                         alertSend(msg)
          else:
              btccloses.append(float(close))
              print("closes")
              print(btccloses)
              if len(btccloses) > RSI_PERIOD:
                    
                    np_closes = numpy.array(btccloses)
                    rsi = talib.RSI(np_closes, RSI_PERIOD)
                    print("all rsis calculated so far")
                    print(rsi)
                    last_rsi = rsi[-1]
                    print("the current rsi is {}".format(last_rsi))

                    if last_rsi > RSI_OVERBOUGHT:
                         
                         print("Overbought! Sell! Sell! Sell!")
                         msg=f"{ticker} are Overbought! Sell! Sell! Sell!"
                         alertSend(msg)
                         
                    if last_rsi < RSI_OVERSOLD:
                         print("Oversold! Buy! Buy! Buy!")
                         msg=f"{ticker} Oversold! Buy! Buy! Buy!"
                         alertSend(msg)
            

              
          


    
    
def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def on_message(ws, message):
    global closes, in_position

    try:
        
        json_message = json.loads(message)
        stream = json_message['stream']
        data = json_message['data']
     #    print('received message')
     #    print(json_message)

        if stream == 'ethusdt@kline_1m':
            rsiAlert(data,"ETH-USD")        

        elif stream == 'btcusdt@kline_1m':
            rsiAlert(data,"BTC-USD")

    except Exception as e:
        print(f'Error in on_message: {e}')

def alertSend(msg):
     notification = Notify()
     
     notification.title = "Trend Reversal Detected !!!!.Check the Market Immedietly"
     notification.message = msg
     notification.application_name="Notification Center"
     notification.send()
    

def background_function():
    ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
    ws.run_forever()

def run_app():
    # Create a process for the background function
    background_process = Process(target=background_function)

    # Start the process
    background_process.start()

    app.run()


############################################################################################
###############################################################################################

@app.route("/")
def hello_world():
    return render_template('index.html')

@app.route("/markets")
def markets():
     return render_template('chart.html')

@app.route("/news")
def news():
     return render_template('news.html')

@app.route("/getnews/<path:name>")
def getnews(name):

    with open('./data/assetsummaries.csv', 'rb') as f:
        result = chardet.detect(f.read())
        df = pd.read_csv('./data/assetsummaries.csv', encoding=result['encoding'])

    # Group the DataFrame by column 'B'
    grouped = df.groupby('Ticker')

    # Extract the group for 'B' == 'x'
    group = grouped.get_group(name)

    # Convert the records in the group to JSON format
    json_data = group.to_json(orient='records')

    # Load the JSON data as a list of dictionaries
    data = json.loads(json_data)
     
     
    return render_template('news.html',data=data)

@app.route("/notification")
def notification():
     return render_template('notification.html')



if __name__ == '__main__':
    freeze_support()
    run_app()