import urllib.parse
from urllib.request import urlopen
from bs4 import BeautifulSoup

class youtube:
    def search(self,text,event):

        query = urllib.parse.quote(text)
        url = "https://www.youtube.com/results?search_query=" + query
        response = urlopen(url)
        html = response.read()
        soup = BeautifulSoup(html, "lxml")

        result = []

        for vid in soup.findAll(attrs={'class':'yt-uix-tile-link'}):

            json_data = {}

            title = vid['title']
            # title = title.replace('-', '')
            # title = title.replace('&', '')
            if len(title) >=40:
                title = title[:37]+'...'
            link = 'https://www.youtube.com' + vid['href']
            id = vid['href'].replace("/watch?v=","");
            if '&' in id:
                id = id.split("&")[0]
            img = "http://img.youtube.com/vi/%s/0.jpg" % id

            json_data['title']=title

            json_data['link']=link
            json_data['img']=img

            # print(json_data)

            result.append(json_data)

        return result



