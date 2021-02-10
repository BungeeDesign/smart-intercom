# smart-intercom
Turns a dumb/anolouge intercom into a smart one by using audio fingerprinting to detect if the intercom has been called, which then sends notifications to other smart devices.

## Usage

Run with Python 2.7 (Planning to refactor to Python 3):

1st argument being the directory of the audio recording.

```sh
python intercom-monitor.py /
```

Recomend use with a Raspberry Pi & GPIO/USB Mic.

Replace all `TOKEN` placeholders with your keys.

APIs Used:

* LiFiX
* Virtual Buttons (Alexa Skill)
* Pushover
* acrcloud.com (Custom Audio Fingerprinting - Extremely accurate)
