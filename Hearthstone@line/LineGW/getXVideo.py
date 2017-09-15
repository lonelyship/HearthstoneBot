import requests
from bs4 import BeautifulSoup

host = "http://123videos.tv/"

def getXvideos(Max):
    xArray=[]
    for i in range(1,Max):
        url = host+'genre/censored/'+'page-'+str(i)+'/'
        r = requests.get(url)
        # print (url)
        # print(r.text)

        soup = BeautifulSoup(r.text, "lxml")

        matches = soup.findAll("div", class_="tn-bxitem")
        for item in matches:
            obj = {}
            title  = item.find("img").get('alt')
            img = item.find("img").get('src')
            link = host+item.find("a").get('href')
            # print(title,img,link)
            obj["title"]=title
            obj['img']=img
            obj['link']=link
            xArray.append(obj)
    # print(len(xArray),xArray)
    return xArray
