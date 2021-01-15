from bs4 import BeautifulSoup
import requests



def main():
    req = requests.get("https://www.wincomparator.com/fr-fr/cotes/basket/usa/nba-id306/")
    soup = BeautifulSoup(req.text, "lxml")
    rows = soup.find_all("div",{"class":"event__item__odd"})
    games_odd = []
    for row in rows:
        game = {
            "home_odd" :1,
            "visitor_odd":1,
        }
        div_home = row.find("span", {"class":"mr-2"})
        if(div_home != None):
            game['home_team'] = div_home.text

        div_visitor = row.find("span", {"class":"ml-2"})
        if(div_visitor != None):
            game['visitor_team'] = div_visitor.text

        odd_div = row.find_all("a", {"class":"event__item__odd"})
        if(odd_div != None):
            if(len(odd_div) >= 2):
                div_home_odd = odd_div[0].find('span')
                div_visitor_odd = odd_div[1].find('span')
                if(div_home_odd != None):
                    game["home_odd"] = float(div_home_odd.text)
                if(div_visitor_odd != None):
                    game["visitor_odd"] = float(div_visitor_odd.text)

        if(game['home_odd'] != 1) & (game['visitor_odd'] != 1):
            games_odd.append(game)

    req = requests.get("https://www.betclic.fr/basket-ball-s4/nba-c13")
    soup = BeautifulSoup(req.text, 'lxml')
    betbox = soup.find_all('div', {"class":"betBox"})
    for row in betbox:
        game = {
                    "home_odd" :1,
                    "visitor_odd":1,
                    'home_team' : None,
                    'visitor_team' : None,
                }

        teams = row.find_all('span', {'class':"betBox_contestantName"})
        if(teams != None):
            if(len(teams) == 2):
                game['home_team'] = teams[0].text.strip()
                game['visitor_team'] = teams[1].text.strip()
        odds = row.find_all('span', {"class":"oddValue"})
        if(odds != None):
            if(len(odds) >= 2):
                game['home_odd'] = float(odds[0].text.replace(',','.'))
                game['visitor_odd'] = float(odds[1].text.replace(',','.'))

        if(game['home_odd'] != 1) & (game['visitor_odd'] != 1):
            games_odd.append(game)

    print(games_odd)

main()