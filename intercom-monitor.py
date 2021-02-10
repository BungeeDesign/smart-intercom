import pyaudio
import math
import struct
import wave
import sys
import os
from time import sleep, time
import base64
import hmac
import hashlib
import requests
from datetime import datetime
import json
import emoji

# Assuming Energy threshold upper than 30 dB
Threshold = 100

SHORT_NORMALIZE = (1.0/32768.0)
chunk = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
swidth = 2
Max_Seconds = 5
TimeoutSignal = ((RATE / chunk * Max_Seconds) + 2)
silence = True
FileNameTmp = 'intercom_audio.wav'
Time = 0
all = []


def sendNotifications():
    # Send Notifications Including Mobile & Alexa (Also Flash LiFiX Light - Visual Indication When At Desk)
    print("[Intercom Monitor] - Sending Notification")

    currentTime = datetime.now()
    payload = {"token": 'INSERT_TOKEN', "user": 'USER_TOKEN', "title": 'Intercom Alert',
               "message": emoji.emojize(':bell:') + ' Intercom Called @ ' + str(currentTime) + emoji.emojize(':bell:')}

    try:
        r = requests.post('https://api.pushover.net/1/messages.json', json=payload,
                          headers={'Content-Type': 'application/json'})
        if r.status_code != 200:
            print('[Intercom Monitor] - Pushover API Response Error', r.status_code)
        else:
            print('[Intercom Monitor] - Notifications Sent')
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)

    # LiFix API Pulse
    token = "LiFIX_TOKEN"
    headers = {
        "Authorization": "Bearer %s" % token,
    }

    data = {
        "period": 2,
        "cycles": 5,
        "color": "green",
    }

    requests.post(
        'https://api.lifx.com/v1/lights/all/effects/pulse', data=data, headers=headers)

    # Send to Alexa API
    requests.get('https://api.virtualbuttons.com/v1?virtualButton=1&accessCode=ACESS_CODE')


def isIntercom():
    access_key = "ACESS_KEY"
    access_secret = "ACESS_SECRET"
    requrl = "http://identify-eu-west-1.acrcloud.com/v1/identify"

    http_method = "POST"
    http_uri = "/v1/identify"
    # default is "fingerprint", it's for recognizing fingerprint, if you want to identify audio, please change data_type="audio"
    data_type = "audio"
    signature_version = "1"
    timestamp = time()

    string_to_sign = http_method+"\n"+http_uri+"\n"+access_key + \
        "\n"+data_type+"\n"+signature_version+"\n"+str(timestamp)

    sign = base64.b64encode(
        hmac.new(access_secret, string_to_sign, digestmod=hashlib.sha1).digest())

    # suported file formats: mp3,wav,wma,amr,ogg, ape,acc,spx,m4a,mp4,FLAC, etc
    # File size: < 1M , You'de better cut large file to small file, within 15 seconds data size is better
    # f = open(sys.argv[1], "rb")
    sample_bytes = os.path.getsize(sys.argv[1])

    files = [
        ('sample', ('intercom_audio.wav', open('intercom_audio.wav', 'rb'), 'audio/mpeg'))
    ]
    data = {'access_key': access_key,
            'sample_bytes': sample_bytes,
            'timestamp': str(timestamp),
            'signature': sign,
            'data_type': data_type,
            "signature_version": signature_version}

    r = requests.post(requrl, files=files, data=data)
    jsonResponse = json.loads(r.text)

    print(jsonResponse)

    if (jsonResponse['status']['msg'] == 'Success'):
        # Intercom Has Been Called
        print('\033[92m' +
              '[Intercom Monitor] - Intercom Called!' + '\033[0m')
        sendNotifications()
    else:
        print('[Intercom Monitor] - No Call')


def GetStream(chunk):
    return stream.read(chunk)


def rms(frame):
    count = len(frame)/swidth
    format = "%dh" % (count)
    # short is 16 bit int
    shorts = struct.unpack(format, frame)

    sum_squares = 0.0
    for sample in shorts:
        n = sample * SHORT_NORMALIZE
        sum_squares += n*n
    # compute the rms
    rms = math.pow(sum_squares/count, 0.5)
    return rms * 1000


def WriteSpeech(WriteData):
    stream.stop_stream()
    # stream.close()
    # p.terminate()
    wf = wave.open(FileNameTmp, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(WriteData)
    wf.close()


def KeepRecord(TimeoutSignal, LastBlock):
    global all
    all.append(LastBlock)
    for i in range(0, TimeoutSignal):
        try:
            data = GetStream(chunk)
        except:
            continue
        # I chage here (new Ident)
        all.append(data)

    print("[Intercom Monitor] - Recording Complete")
    data = ''.join(all)
    print("[Intercom Monitor] - Writing To File")
    WriteSpeech(data)

    # After Writing The Audio File Call isIntercom() for Intercom detection
    isIntercom()

    silence = True
    Time = 0
    # Restart Stream
    stream.start_stream()
    # Clear Previous Audio Data/State
    all = []
    listen(silence, Time)


def listen(silence, Time):
    print("[Intercom Monitor] - Actively Monitoring")
    while silence:
        try:
            input = GetStream(chunk)
        except Exception as e:
            print('[Intercom Monitor Error] - ', e)
            continue
        rms_value = rms(input)
        print('[Intercom Monitor] - RMS:', rms_value)
        if (rms_value > Threshold):
            print('\033[92m' +
                  '[Intercom Monitor] - Threshold Detection' + '\033[0m')
            silence = False
            LastBlock = input
            print("[Intercom Monitor] - Starting Recording")
            KeepRecord(TimeoutSignal, LastBlock)


p = pyaudio.PyAudio()

stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                output=True,
                frames_per_buffer=chunk)

listen(silence, Time)
# sendNotifications()
