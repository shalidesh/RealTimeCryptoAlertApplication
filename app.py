from flask import Flask,render_template, url_for, request,flash,redirect,Response,send_from_directory,session,jsonify
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

from binance.client import Client
from flask_cors import CORS
from datetime import datetime

import os, csv
import talib
import yfinance as yf
import pandas
from patterns import candlestick_patterns

from flask_pymongo import PyMongo
import uuid
from passlib.hash import pbkdf2_sha256
from flask_session import Session


from chatBot.chat import get_response


# specify path to save the model and tokenizer
path = './models/t5-small/'

# tokenizer = T5Tokenizer.from_pretrained(path)
# model = T5ForConditionalGeneration.from_pretrained(path)

app = Flask(__name__)

summery_path='./data/assetsummaries.csv'
monitored_tickers=[]
SOCKET = "wss://stream.binance.com:9443/stream?streams=ethusdt@kline_1m/btcusdt@kline_1m"

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


app.config["SECRET_KEY"] = "db24c608640f5034b30b8e1e1eb5618ed0ffdbf5"
app.config["MONGO_URI"] = "mongodb://localhost:27017/cryptoapp"
db = PyMongo(app).db

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
        print('received message')
        print(json_message)

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

@app.route("/chat",methods=['POST'])
def chat():
    text=request.get_json().get("message")
    print(text)
    reponse=get_response(text)
    message={"answer":reponse}
    print(message)
    return jsonify(message)

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

@app.route("/login")
def loginPage():
     return render_template('login.html')

@app.route('/user/login', methods=['POST'])
def login():
    email = request.form["email"]
    password = request.form["password"]
    user = db.users.find_one({"email": email, "password": password})
    if user :
        session["name"] = request.form.get("email")
        return redirect('/')
    else:
        return redirect('/login')

@app.route("/signup")
def signupPage():
     return render_template('signup.html')

@app.route("/logout")
def logout():
    session["name"] = None
    return redirect('/')

@app.route('/user/signup', methods=['POST'])
def signup():
  
  user = {
      "_id": uuid.uuid4().hex,
      "name": request.form.get('name'),
      "email": request.form.get('email'),
      "password": request.form.get('password')
    }


  if db.users.insert_one(user):
       return redirect('/login')
  else:

    return jsonify({ "error": "Signup failed" }), 400


@app.route('/snapshot')
def snapshot():
    rows=[]
    with open('data/symbols.csv') as file:
        csvreader = csv.reader(file)
        # header = next(csvreader)
        for row in csvreader:
            rows.append(row[0])
            symbol=row[0]
            start_date = datetime.datetime(2020, 1, 1)
            end_date = datetime.datetime.now()

            data = yf.download(symbol, start=start_date, end=end_date)

            data.to_csv('data/CryptoData/{}.csv'.format(symbol))

    return  render_template('patternresult.html',info1=rows)



@app.route("/patterndetect")
def patterndetect():
    pattern  = request.args.get('pattern', False)
    stocks = {}

    with open('data/symbols.csv') as f:
        for row in csv.reader(f):
            try:
                stocks[row[0]] = {'company': row[0]}
            except Exception as e:
                print(e)

    if pattern:
        for filename in os.listdir('data/CryptoData'):
            df = pandas.read_csv('data/CryptoData/{}'.format(filename))
            print(df.tail(2))
            pattern_function = getattr(talib, pattern)
            symbol = filename.split('.')[0]
            lastdate=df.tail(1)['Date'].values[0]
            print(lastdate)

            try:
                results = pattern_function(df['Open'], df['High'], df['Low'], df['Close'])
                last = results.tail(1).values[0]

                if last > 0:
                    stocks[symbol][pattern] = 'bullish'
                    stocks[symbol]["date"] = lastdate
                elif last < 0:
                    stocks[symbol][pattern] = 'bearish'
                    stocks[symbol]["date"] = lastdate
                else:
                    stocks[symbol][pattern] = None
                    stocks[symbol]["date"] = lastdate
            except Exception as e:
                print('failed on filename: ', filename)
    print(stocks)
    # print(pattern)
    # return jsonify(stocks)
    return render_template('patterndetect.html', candlestick_patterns=candlestick_patterns, stocks=stocks, pattern=pattern)
    



if __name__ == '__main__':
    freeze_support()
    run_app()