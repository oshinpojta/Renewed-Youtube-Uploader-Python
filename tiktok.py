
from idm import IDMan
import asyncio
from pyppeteer import launch
import time
import os
import re #regex
import pyautogui
import webbrowser
import random
pyautogui.FAILSAFE = False
def upload_tiktok():
  downloader = IDMan()
  rewindzap_search = ["joblessgarrett","samseats","thelaughfactory","no1standupcomedy","comedygoats","marvelinterviews","collegehumor","carpoolkaraoke","thebestoff","trent_of_all_trades","deliciousaus","foodinspiration6868","2012ferrari","best of tiktok","best of tiktok","funny home videos","funny pets","kkokdiger","deedawww","_the_faded_line_","devourpower","jdrek_airsoft","glitchbox","quotes","pickup lines","radiobigmack3","soggyhealer3.0","myahiddengems","cr8tv","painful_cringe","full_squad_gaming","meme_hub9156","weavile ","thefunmaster3000","bartendersfbay","avacabro4","family guy memes","steve harvey","wave.tv","funny","the family guy","quagmire","anime","cars","tiktok","challenge","cringe","foodie","hot","viral","football","haunted","wierd","trending","UFC MMA","Cringe Football"]
  bunny_girl_search = ["changellenge","cherrybakewell92","kylayese","cinnannoe","fegalvao_","Ana Aide Blanco Hern","dayanababy___","fafafitness11","audreytrullinger","lacolombianadetiktok2","wetmodels","Bikini Models","mia.federico","delightfullydani","aesthedlts","bts edits","arigameplays","soylizbethrz","clara00ellis","esidentevil_fan_15","ser_twiglius","onlycosvickye","babybells___","miakhalifa","imbaddiesonly","dan bilzerian","sainttraps88","lnkjeohge2","darediva_","slaytillltheam","kodeeleeallbon_","savannahhsummerr","serriacruz","u.miniloona","thisaccisdedh3h3","rachel.gil","missbricosplay","taylorsdiary2","ustinavalentine","giannachristiine","meganjewells","Ashley Elliott","gabbyb_music","adrianaocarizb","hottie","babes","tiktok girls","beautiful girls","sexy","russian girls","models","hollywood actress","bikini","no bra challenge","russian girls","american girls","victoria secret models","american models","english models","anime waifu","cosplay girls","bts","korean girls","anime girls","hot girls anime edits","latina",""]
  sigma_search = ["thequotebibles","only for men","muscle","gym","fitness","alpha mindset","perfect men","motivational videos","elon musk","earn money","motivation","life quotes","godfather","life quotes","sigma grindset anime","sigma","sigma shelby","peaky blinders","sigma movies","sigma males"]
  rigzed_search = ["call of duty","apex legends","pubg","best kills","montage","funny gaming clips","VR Gaming","Ninja Gaming","Free Fire","ESports","God Of War","Best Gaming Clips","Shroud","Drdisrespect","Best Plays of Gaming","Fortnite","GTA 5","Best Of GTA 5","Valorant","Gaming Matches","Assassins Creed","New games","Elon Musk","Gaming News","Gadgets","Tech News","New Tech","New games","Gadgets","Tech News","New Tech","Gaming Technology","News Tech","Best Racing Games","Best Battle Royal","Best mmorpg","Messi","Ronaldo","Viral","Trending","Best Playes of Battle Royal","Top Kills in Pubg Fortnite Apex Legends Call Of Duty","videogame", "pcgaming", "twitch gamers" "gaminglife" "xboxonex","Minecraft","funny sports","fh5clips","funny gaming","full_squad_gaming","cars","jdrek airsoft","cringe Gameplays","Funny GamePlays","Popular Gameplays"]
  for i in range(0,4) :
    print("i:-",i)
    #keep count of search
    count = 0
    file = open("CountSearch"+'{}'.format(i)+".txt")
    for line in file:
        fields = line.strip().split()
        count = fields[0]
        print(count)
    file.close()
    num = int(count)+1
    if i==0:
      tags = rigzed_search
      num = num%len(tags)
      tag_name = tags[num]
      tiktok_web_url = "https:///www.tiktok.com//search//video?q="+tag_name
      tiktok_html_element = "div.tiktok-1soki6-DivItemContainerForSearch.e19c29qe9"

      pyautogui.sleep(10)
      webbrowser.open('https://studio.youtube.com/', new = 1)
      pyautogui.sleep(30)
      pyautogui.click(1325,100) #account
      pyautogui.sleep(10)
      pyautogui.click(1325, 300) #switch account
      pyautogui.sleep(10)
      pyautogui.click(1250, 235) #select account
      pyautogui.sleep(20)
      pyautogui.hotkey('ctrl', 'w')
      pyautogui.sleep(10)

    if i==1:
      tags = rewindzap_search
      num = num%len(tags)
      tag_name = tags[num]
      tiktok_web_url = "https:///www.tiktok.com//search//video?q="+tag_name
      tiktok_html_element = "div.tiktok-1soki6-DivItemContainerForSearch.e19c29qe9"

      pyautogui.sleep(10)
      webbrowser.open('https://studio.youtube.com/', new = 1)
      pyautogui.sleep(30)
      pyautogui.click(1325,100) #account
      pyautogui.sleep(10)
      pyautogui.click(1325, 300) #switch account
      pyautogui.sleep(10)
      pyautogui.click(1250, 365) #select account
      pyautogui.sleep(20)
      pyautogui.hotkey('ctrl', 'w')
      pyautogui.sleep(10)
      
    if i==2:
      tags = bunny_girl_search
      num = num%len(tags)
      tag_name = tags[num]
      tiktok_web_url = "https:///www.tiktok.com//search//video?q="+tag_name
      tiktok_html_element = "div.tiktok-1soki6-DivItemContainerForSearch.e19c29qe9"
      pyautogui.sleep(10)
      webbrowser.open('https://studio.youtube.com/', new = 1)
      pyautogui.sleep(30)
      pyautogui.click(1325,100) #account
      pyautogui.sleep(10)
      pyautogui.click(1325, 300) #switch account
      pyautogui.sleep(10)
      pyautogui.click(1250, 425) #select account
      pyautogui.sleep(20)
      pyautogui.hotkey('ctrl', 'w')
      pyautogui.sleep(10)

    if i==3:
      tags = sigma_search
      num = num%len(tags)
      tag_name = tags[num]
      tiktok_web_url = "https://www.tiktok.com/search/video?q="+tag_name
      tiktok_html_element = "div.tiktok-1soki6-DivItemContainerForSearch.e19c29qe9"
      pyautogui.sleep(10)
      webbrowser.open('https://studio.youtube.com/', new = 1)
      pyautogui.sleep(30)
      pyautogui.click(1325,100) #accounts
      pyautogui.sleep(10)
      pyautogui.click(1325, 300) #switch account
      pyautogui.sleep(10)
      pyautogui.click(1250, 685) #select account
      pyautogui.sleep(20)
      pyautogui.hotkey('ctrl', 'w')
      pyautogui.sleep(10)

    pyautogui.moveTo(680,12)
    string_count = '{}'.format(num)
    fileptr = open("CountSearch"+'{}'.format(i)+".txt","w")  
    fileptr.write(string_count)
    fileptr.close()
    url_list = [] #for appending tiktotk html element urls
    title_list = []
    while True:
      try:
        async def main():
            print("Launching Browser....")
            # launch chromium browser in the background
            browser = await launch({"headless": False, "args": ["--start-maximized"],"executablePath":"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe", "userDataDir":"C:\\Users\\Ritesh\\Documents\\User Data"})
            # open a new tab in the browser
            page = await browser.newPage()
            print("Getting Tiktok.com .....")
            await page.goto(tiktok_web_url)
            #await page.goto(")
            #await page.setViewport({"width": 1600, "height": 900})
            time.sleep(120)
            v = await page.querySelectorAll(
              tiktok_html_element
            )
            v = v[:2]
            print("Extracted DIVs : ",len(v))
            ay = 0
            for vid in v:
              ay = ay+1
              await vid.hover()
              time.sleep(20)
              #
              s = await vid.querySelector("video")
              t = await vid.querySelector("span.tiktok-j2a19r-SpanText.efbd9f0")
              src = await s.getProperty("src")
              get_title = await t.getProperty("textContent")
              url = await src.jsonValue()
              print(url)
              title_now = await get_title.jsonValue()
              url_list.append(url)
              title_list.append(title_now)
            await browser.close()
          
            print("URLs list ready...browser closed !")
        asyncio.get_event_loop().run_until_complete(main())
      except Exception as e :
        os.system("taskkill /im chrome.exe /f")
        print(e)
        print("EXCEPTION OCCURRED >>>>>>>>>> RETRYING !!!")
      else:
        break
      
    print("Starting : Tiktok Download .... for you ")
    #
    #upload one by one 3 vids
    dir_path = "c:\\users\\Ritesh\\desktop\\python reddit youtube\\vids"
    print("Starting Upload to YouTube....")
    count_upload = 0
    count =  0
  
    for url_num in range(0,len(url_list)):
      url = url_list[url_num]
      title = title_list[url_num]
      if count_upload == 2:
        break
      else:
        count_upload = count_upload+1
      downloader.download(url, dir_path, output="output.mp4", referrer=None, cookie=None, postData=None, user=None, password=None, confirm = False, lflag = None, clip=False)
      #keep count of videos
      file = open("CountTiktokVid"+'{}'.format(i)+".txt")
      for line in file:
          fields = line.strip().split()
          count = fields[0]
          print(count)
      file.close()
      num = int(count)+1
      string_count = '{}'.format(num)
      fileptr = open("CountTiktokVid"+'{}'.format(i)+".txt","w")  
      fileptr.write(string_count)
      fileptr.close()
      title = title[:60]
      if i==0:
        title = title+" Best Of Gaming Tech Videos #"+string_count
      elif i==1:
        title = title+" Best Of Amazing Videos #"+string_count
      elif i==2 :
        title = title+" Best Of Tiktok Videos #"+string_count
      else :
        title = title+" #BillionaireGrindset #Motivation #"+string_count
      print(title)
      pyautogui.sleep(10)
      webbrowser.open('https://studio.youtube.com/', new = 1)
      pyautogui.sleep(30)
      pyautogui.click(1210,100) #create
      pyautogui.sleep(10)
      pyautogui.click(1150, 145) #upload
      pyautogui.sleep(10)
      pyautogui.click(670,535) # select files
      pyautogui.sleep(10)
      pyautogui.click(215,140) # file choose
      pyautogui.sleep(10)
      pyautogui.click(520,450) # open
      pyautogui.sleep(10)
      pyautogui.click(x=264, y=358, clicks=2) #double click title paste
      pyautogui.sleep(10) 
      pyautogui.write(title)
      pyautogui.sleep(10)
      pyautogui.click(264, 464) #paste description
      pyautogui.write("Best of Trending Videos Only For You   \n")
      pyautogui.sleep(10)
      pyautogui.click(1115, 690) #next
      pyautogui.sleep(10)
      pyautogui.click(1115, 690) #next
      pyautogui.sleep(10)
      pyautogui.click(1115, 690) #next
      pyautogui.sleep(10)
      pyautogui.click(1115, 690) #next
      pyautogui.sleep(300)
      pyautogui.hotkey('ctrl', 'w')
      pyautogui.sleep(10)
      os.system("del /f /q vids\\output.mp4")
      print("deleted output.mp4")
      pyautogui.moveTo(680,12)
    '''
    #upload 3 vids by merging
    for l in range(len(url_list)-4,len(url_list)-1):
      url = url_list[l]
      name = '{}'.format(l)+".mp4"
      downloader.download(url, dir_path, output=name, referrer=None, cookie=None, postData=None, user=None, password=None, confirm = False, lflag = None, clip=False)
      time.sleep(30)
      fileptr = open("videonames.txt","a")  
      fileptr.write("file "+name+"\n")
      fileptr.close()
      time.sleep(5)

    os.system("move vids\\*.mp4")
    time.sleep(20)
    os.system("ffmpeg -f concat -i videonames.txt -c copy vids\\output.mp4")
    time.sleep(20)
    os.system("del /f /q *.mp4")
    os.system("del /f /q videonames.txt")
    print("deleting all downloaded tiktok files & videonames.txt...")
    #keep count of videos
    file = open('CountTiktokVid'+'{}'.format(i)+'.txt')
    for line in file:
        fields = line.strip().split()
        count = fields[0]
        print(count)
    file.close()
    num = int(count)+1
    string_count = '{}'.format(num)
    fileptr = open("CountTiktokVid"+'{}'.format(i)+".txt","w")  
    fileptr.write(string_count)
    fileptr.close()
    title = title_list[len(title_list)-4]
    title = title[:50]+"..... | "
    if i==0:
      title = title+"Trending Gaming Tech Videos #"+string_count
    elif i==1:
      title = title+"Amazing Awesome Videos #"+string_count
    elif i==2 :
      title = title+"Tiktok Videos #"+string_count
    else :
      title = title+" | #BillionaireGrindset #Motivation #"+string_count
    print(title)
    pyautogui.sleep(10)
    webbrowser.open('https://studio.youtube.com/', new = 1)
    pyautogui.sleep(20)
    pyautogui.click(1210,100) #create
    pyautogui.sleep(10)
    pyautogui.click(1150, 145) #upload
    pyautogui.sleep(10)
    pyautogui.click(670,535) # select files
    pyautogui.sleep(10)
    pyautogui.click(215,140) # file choose
    pyautogui.sleep(10)
    pyautogui.click(520,450) # open
    pyautogui.sleep(10)
    pyautogui.click(x=264, y=358, clicks=2) #double click title paste
    pyautogui.sleep(10) 
    pyautogui.write(title)
    pyautogui.sleep(10)
    pyautogui.click(264, 464) #paste description
    pyautogui.write("Best Of Videos Only For You   \n")
    pyautogui.sleep(10)
    pyautogui.click(1115, 690) #next
    pyautogui.sleep(10)
    pyautogui.click(1115, 690) #next
    pyautogui.sleep(10)
    pyautogui.click(1115, 690) #next
    pyautogui.sleep(10)
    pyautogui.click(1115, 690) #next
    pyautogui.sleep(300)
    pyautogui.hotkey('ctrl', 'w')
    pyautogui.sleep(5)
    os.system("del /f /q vids\\output.mp4")
    print("deleted output.mp4")
    '''
    if i==3:
      pyautogui.sleep(10)
      webbrowser.open('https://studio.youtube.com/', new = 1)
      pyautogui.sleep(30)
      pyautogui.click(1868,100) 
      pyautogui.sleep(10)
      pyautogui.click(1865, 300) 
      pyautogui.sleep(10)
      pyautogui.click(1865, 620) 
      pyautogui.sleep(20)
      pyautogui.hotkey('ctrl', 'w')
      pyautogui.sleep(10)

    pyautogui.moveTo(680,12)

upload_tiktok()