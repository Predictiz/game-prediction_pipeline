from pymongo import MongoClient
import os
import time
import datetime


class AtlasDB:
    def __init__(self, season):
        self.client = MongoClient(os.environ["PREDICTIZ_CREDENTIALS"])
        dblist = self.client.list_database_names()
        if "season_" + season in dblist:
            #raise IOError("Cette base de donnée existe déjà.")
            print("attention, cette base de donnée existe déja, vous avez 5 secondes pour annuler l'opération")
            time.sleep(5)
        db = self.client["season_" + season]
        self.table_team = db["team"]
        self.table_player = db["player"]
        self.table_game = db["game"]
        self.table_player_stats = db["playerStats"]
        self.table_history = db["prediction_history"]
        print("Atlas MongoDB connected")

    def add_team(self, team):
        exist = self.table_team.find_one({"nick": team['nick']})
        if(exist == None):
            self.table_team.insert_one(team)

    def add_game(self, game):
        visitor = self.table_team.find_one({"nick": game["visitor_nick"]})
        home = self.table_team.find_one({"nick": game["home_nick"]})
        existing_game = self.table_game.find_one({"csk": game["csk"]})
        # Insert in Games
        if(existing_game is not None):
            stats = self.table_history.find_one({"ide":"games_2021"})
            try:
                game["home_odd"] = existing_game["home_odd"]
                game["visitor_odd"] = existing_game["visitor_odd"]
                print("")
            except Exception:
                print("no odd for this game")
                game["home_odd"] = 1
                game["visitor_odd"] = 1
            try: 
                home_win = existing_game['home_win_bet']
                no_bet = existing_game['no_bet']
                visitor_win = existing_game['visitor_win_bet']
                game['home_win_bet'] = home_win
                game['no_bet'] = no_bet
                game['visitor_win_bet'] = visitor_win
                balance = 0
                games_predicted = 0
                games_misspredicted = 0
                if(stats != None):
                    balance = stats["balance"]
                    games_predicted = stats["games_predicted"]
                    games_misspredicted = stats["games_misspredicted"]

                if(home_win > 0.5):
                        game['earned'] = -10.0
                        if(game['winner'] == 1):
                            balance += 10.0 * game["home_odd"]
                            games_predicted += 1
                            game['earned'] += 10.0 * game["home_odd"]
                        else:
                            games_misspredicted += 1
                        balance += -10.0
                        game['betted'] = 1

                elif(visitor_win > 0.5):
                        game['earned'] = -10.0
                        if(game['winner'] == 0):
                            balance += 10.0 * game["visitor_odd"]
                            games_predicted += 1
                            game['earned'] += 10.0 * game["visitor_odd"]
                        else:
                            games_misspredicted +=1
                        balance += -10.0
                        game['betted'] = 0

                else:
                    game['betted'] = -1
                    game['earned'] = 0

                game['earned'] = round(game['earned'],2)
                balance = round(balance, 2)
                if(stats == None):
                    self.table_history.insert_one({
                        "balance":balance,
                        "games_predicted":games_predicted,
                        "games_misspredicted":games_misspredicted,
                        "ide":"games_2021"
                    })
                else:
                    self.table_history.update_one({"ide":"games_2021"},
                    {
                        "$set":{
                            "balance":balance,
                            "games_predicted":games_predicted,
                            "games_misspredicted":games_misspredicted,
                        }
                    })
            except Exception:
                print(Exception, "this game was not predicted")


            self.table_game.delete_one({"csk": game["csk"]})

        if(visitor is not None) & (home is not None):
            game["visitor_id"] = visitor["_id"]
            game["home_id"] = home["_id"]
            game["home_name"] = home["name"]
            game["visitor_name"] = visitor["name"]
            retour = self.table_game.insert_one(game)

            # Update GamesIds in team
            self.table_team.update_one({"nick": game["visitor_nick"]}, {"$push": {"gameIds": retour.inserted_id}})
            self.table_team.update_one({"nick": game["home_nick"]}, {"$push": {"gameIds": retour.inserted_id}})


    def add_player(self, name):
        exist = self.table_player.find_one({"name": name})
        if exist is None:
            retour = self.table_player.insert_one({"name": name})
            return retour.inserted_id
        else:
            return exist['_id']

    def add_player_stats(self, game_csk, player_name, team_name, stats):
        team = self.table_team.find_one({"nick": team_name})
        game = self.table_game.find_one({"csk": game_csk})
        player = self.table_player.find_one({"name": player_name})
        if player is None:
            player_id = self.add_player(player_name)
            # print("PLAYER IS NONE, ADD PLAYER : "+str(player_id))
        else:
            player_id = player["_id"]
            # print("PLAYER IS NOT NONE, get id : "+str(player_id))

        
        if (team is not None) & (game is not None):
            # Insert in Player Stats
            self.table_player_stats.insert_one(
                {"player_id": player_id, "game_id": game["_id"], "team_id": team["_id"], "stats": stats})
            # print("stat added To the db")

            # Update rosterIds from the team if necessary
            roster_ids = team["rosterIds"]
            if player_id not in roster_ids:
                self.table_team.update_one({"nick": team_name}, {"$push": {"rosterIds": player_id}})
