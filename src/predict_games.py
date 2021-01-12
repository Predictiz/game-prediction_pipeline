from load_data_from_db import DB_Access
import pandas as pd
import pickle5 as pickle
from keras.models import load_model
import numpy as np

def main():
    year = "2021"
    db = DB_Access(year)

    df = load_games_data(db,year)
    print("here")

    # y = df.pop('win')
    home_names = df.pop('home_name')
    visitor_names = df.pop('visitor_name')
    home_odd = df.pop('home_odd')
    visitor_odd = df.pop('visitor_odd')
    game_csk = df.pop('csk')
    X = df

    bin_path = str(8)
    ##LOADING MODELS
    k_near = pickle.load(open("model/"+bin_path+"/k-nearest.model", 'rb'))
    l_regression = pickle.load(open("model/"+bin_path+"/logisitic-regression.model", 'rb'))
    n_bayes = pickle.load(open("model/"+bin_path+"/naive_bayes.model", 'rb'))
    svm = pickle.load(open("model/"+bin_path+"/svm.model", 'rb'))
    n_network = load_model("model/"+bin_path+"/neural-network.h5")

    n_network_bet = load_model("model/betting_8/odds_loss.h5", compile=False)
   
    
    summ = 0
    games = 0
    a = []
    b = []
    c = []
    d = []
    e = []
    for index, row in X.iterrows():
        
        a.append( predict_from_model(k_near,[row])[0])
        b.append( predict_from_model(l_regression,[row])[0])
        c.append( predict_from_model(svm,[row])[0])
        d.append( predict_from_model(n_bayes,[row])[0])
        e.append( predict_from_model(n_network,np.array([row]))[0][0])
      


    df['k-near_pred'] = a  
    df['l-regression_pred'] = b
    df['svm_pred'] = c
    df['n-bayes_pred'] = d
    df['n-network_pred'] = e
    df['home_odd'] = home_odd
    df['visitor_odd'] = visitor_odd
    
    
    final = pd.DataFrame()
    for index, row in X.iterrows():
        game_pred = {}
        res = predict_from_model(n_network_bet,np.array([row]))[0]
        game_pred['home_win'] = res[0]
        game_pred['visitor_win'] = res[1]
        game_pred['no_bet'] = res[2]
        final = final.append(game_pred, ignore_index=True)
        # print(res[0], res[1], res[2])
    final['csk'] = game_csk
    final['home_name'] = home_names
    final['visitor_name'] = visitor_names
    final['home_odd'] = home_odd
    final['visitor_odd'] = visitor_odd
    final['home_win_probability'] = e
    print(final)
    final.to_csv("predictions.csv",sep=';')
    for index, game in final.iterrows():
        db.save_to_db(game)
        print(game)



def predict_from_model(model, data, index=False):
    result = model.predict(data) 
    return result



def load_games_data(db, year):
    print("getting games")
    games = db.get_games_not_played()
    indice = 0
    data = {}
    for game in games:
            print(indice)
            home_team = db.get_team(game['home_nick'])
            visitor_team = db.get_team(game['visitor_nick'])

            home_stats = db.get_team_stats_aggregate_before_game(game['home_nick'], game['date'])
            visitor_stats  = db.get_team_stats_aggregate_before_game(game['visitor_nick'], game['date'])

            home_players, home_bench_players = db.get_players_grades_aggregate(home_team['_id'], game['date'], game['_id'])
            visitor_players, visitor_bench_players = db.get_players_grades_aggregate(visitor_team['_id'], game['date'], game['_id'])
            

            previous_games = db.get_same_game_previous_stats(game['date'],game['home_nick'], game['visitor_nick'])
                      
            if(home_stats is not None) & (visitor_stats is not None) & (home_players is not None) & (visitor_players is not None):
                
                total_game_stats = {}
                for stat in home_stats:
                    total_game_stats[stat] = home_stats[stat] - visitor_stats[stat]
                
                total_players_stat = {}
                for stat in home_players:
                    total_players_stat[stat] = home_players[stat] - visitor_players[stat]

                total_players_bench_stat = {}
                for stat in home_bench_players:
                    total_players_bench_stat[stat] = home_bench_players[stat] - visitor_bench_players[stat]
                
                #Ecriture des entêtes
                if(indice == 0):
                    data['csk'] = []
                    data['home_elo_probability'] = []
                    data['home_name'] = []
                    data['visitor_name'] = []
                    
                    for h in total_game_stats:
                        data['h-v_'+str(h)] = []

                    for h in previous_games:
                        data['prev_'+str(h)] = []

                    for h in total_players_stat:
                        data['h-v-5_'+str(h)] = []
                    
                    for h in total_players_bench_stat:
                        data['h-v-bench_'+str(h)] = []

                    data['home_odd'] = []
                    data['visitor_odd'] = []

                    
                # Ecriture des données
                data['csk'].append(game['csk'])
                data['home_elo_probability'].append(game['home_win_probability'])
                data['home_name'].append(home_team['name'])
                data['visitor_name'].append(visitor_team['name'])       

                for h in total_game_stats:
                    data['h-v_'+str(h)].append(total_game_stats[h])
                    
                for h in previous_games:
                    data['prev_'+str(h)].append(previous_games[h])
                
                
                for h in total_players_stat:
                    data['h-v-5_'+str(h)].append(total_players_stat[h])
               
                for h in total_players_bench_stat:
                    data['h-v-bench_'+str(h)].append(total_players_bench_stat[h])

                try:
                    data['home_odd'].append(game['home_odd'])
                except Exception:
                    print("e")
                    data['home_odd'].append(1)
                try:
                    data['visitor_odd'].append(game['visitor_odd'])
                except Exception:
                    print("e")
                    data['visitor_odd'].append(1)

                indice += 1
            
    df = pd.DataFrame(data=data)
    return df




main()

