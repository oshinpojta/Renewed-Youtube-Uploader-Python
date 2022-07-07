import os
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
import datetime
from datetime import datetime
import pyautogui

from tiktok import upload_tiktok

now = datetime.now()
print(now)
sched = BlockingScheduler()
def model():
    pyautogui.click(x=1325,y=100, clicks=2)
    pyautogui.sleep(60)
    pyautogui.click(415,540)
    pyautogui.sleep(10)
    color = (42, 156, 243)
    print(pyautogui.pixel(825,320))
    if not (pyautogui.pixelMatchesColor(825, 320, color, tolerance = 30)):
        pyautogui.click(825,320)
    pyautogui.sleep(10)
    print(pyautogui.pixel(825,320))
    pyautogui.click(1095,125)
    pyautogui.sleep(10)
    os.system("tiktok.bat")
    
pyautogui.click(x=1325,y=100, clicks=2)
pyautogui.sleep(60)
pyautogui.click(415,540)
pyautogui.sleep(10)
color = (42, 156, 243)
print(pyautogui.pixel(825,320))
if not (pyautogui.pixelMatchesColor(825, 320, color, tolerance = 30)):
    pyautogui.click(825,320)
pyautogui.sleep(10)
print(pyautogui.pixel(825,320))
pyautogui.click(1095,125)
pyautogui.sleep(10)
upload_tiktok()
sched.add_job(model, 'interval', hours=12, misfire_grace_time=3600)
sched.start()