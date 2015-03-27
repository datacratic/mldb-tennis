import os,socket,time,csv,json,datetime
from datetime import datetime
from copy import deepcopy
import json


tournaments = {}
players ={}
allHistory = {}
trainingYear = 2014
thePlayer = "Federer R."

def print_history(theHistory):
    # print all history
    for theDate in sorted(theHistory):
        print "Player info @ ", datetime.utcfromtimestamp(float(theDate)), " epoch : ", theDate
        for player in theHistory[theDate]:
            print "\t Player: ", player, " info ", theHistory[theDate][player]

def printTournaments():
    # Print out tournament info
    for tournament in tournaments:
        print "Tournament = ", tournament
        print "\t ", tournaments[tournament]["Surface"]
        print "\t ", tournaments[tournament]["Court"]
        print "\t ", tournaments[tournament]["Best of"]
        print "\t ", tournaments[tournament]["Series"]
        print "\t ", tournaments[tournament]["rounds"]

def generate_stats_tables(tournaments,players):

    print "calling generate stats tables asdfasdf"
    dataDir = "data/"
    print "the data directory is " + dataDir

#   year = 2000
    numLines = 0
    prevDate = int(datetime.now().strftime('%s'))
    for year in range(2000,2015):
        print "The year is :" + str(year)
        fileToProcess = dataDir + "ATP_" + str(year) + ".csv"
        print "The file to process is " + fileToProcess
        csvFile = open(fileToProcess, 'r')
        firstLine = csvFile.readline()
        print "the first line is :" + firstLine
        for line in csvFile:
            #print line
            nextLine = line.split(",")

            matchDate = int(datetime.strptime(nextLine[3][1:-1],'%m/%d/%Y').strftime('%s'))
#           print "the date is ", matchDate, ":" , datetime.utcfromtimestamp(matchDate)
            tournament = nextLine[2][1:-1]
            #print "Tournament :" , tournament
            round = nextLine[7][1:-1]
            surface = nextLine[6][1:-1]
            court = nextLine[5][1:-1]
            bestof = nextLine[8][1:-1]
            series = nextLine[4][1:-1]
            if not tournament in tournaments:
                #print "tournament:", tournament, " not seen yet"
                tournaments[tournament] = {}
                tournaments[tournament]["rounds"] = {round:True}
                tournaments[tournament]["Surface"] = surface;
                tournaments[tournament]["Court"] = court;
                tournaments[tournament]["Best of"] = bestof;
                tournaments[tournament]["Series"] = series;
            else:
                # before adding a round make sure that it is not already there
                if not round in tournaments[tournament]["rounds"]:
                    #print "Adding round ", round , " to tournament ", tournament
                    tournaments[tournament]["rounds"][round] = True
#           print "prev date = ", prevDate , " matchDate = ", matchDate
            if matchDate != prevDate:
                #
                # now we add these stats to the appropriate date entry
                # Note that if the date already exists then it is overwritten with more up to date stats
                # Since the source data is sorted by date at any given point in time we have the stats for
                # players at that point in time
                #
#               print "change of date at ", datetime.utcfromtimestamp(float(matchDate))
                playerSnapshot = dict()

                # we don't do a deepcopy because it's incredibly slow....
                for (player,stats) in players.iteritems():
                    statsCopy = {}
                    for k in stats:
                        #print k,":",stats[k]
                        statsCopy[k] = stats[k]
                    playerSnapshot[player] = statsCopy

                allHistory[matchDate] = playerSnapshot
                prevDate = matchDate

            winner = nextLine[9][1:-1]
            loser = nextLine[10][1:-1]
            wrank = nextLine[11][1:-1]
            lrank = nextLine[12][1:-1]
            #update generate non-Federer related statistics
            if not loser in players:
#               print "First time we see player ", loser
                players[loser] = {"numGames":1, "numWins":0, "numGamesVsFed":0, "numWinsVsFed":0,"rank":lrank}
            else:
                players[loser]["numGames"]+=1
                players[loser]["rank"] = lrank

            if not winner in players:
#               print "First time we see player ", winner
                players[winner] = {"numGames":1, "numWins":1, "numGamesVsFed":0, "numWinsVsFed":0,"rank":wrank}
            else:
                players[winner]["numGames"]+=1
                players[winner]["numWins"]+=1
                players[winner]["rank"] = wrank
            # now update Federer-specific stats
            if winner == "Federer R.":
#               print "Federer is winner against ", loser
                players[loser]["numGamesVsFed"]+=1
            elif loser == "Federer R.":
#               print "Federer loses to ", winner
                players[winner]["numWinsVsFed"]+=1
                players[winner]["numGamesVsFed"]+=1

    #print_history(allHistory)


def get_player_stats(history, player, ts):

    print " get_player_stats for player  :", player, " at time ", ts, ":", datetime.utcfromtimestamp(ts)
    # look for the history at the specified time
    if history.get(ts) == None:
        print "no history at time " ,ts
        return None
    snapshot = history[ts]
    if snapshot.get(player) == None:
        print "no stats for player ", player
        return None
    playerStats = snapshot[player]
#    print "stats for player ", player, ":", playerStats
    return playerStats



def load_dataset(dataset, thePlayer):
#    global get_player_stats
#    global datetime
    print "Entering load_dataset...."
    dataDir = "data/"
    year = 2000
    num_lines = 0

    for year in range(2000,2015):
        fileToProcess = dataDir
        print "The year is :" + str(year)
        fileToProcess = dataDir + "ATP_" + str(year) + ".csv"
        print "The file to process is " + fileToProcess
        csvFile = open(fileToProcess, 'r')
        firstLine = csvFile.readline()
        print "the first line is :" + firstLine
        cols = firstLine.split(",")
        # cols are as follows
        # For the year from 2000 to 2004 (inclusive) there WPts and LPts are missing
        # "ATP","Location","Tournament","Date","Series","Court","Surface","Round","Best of","Winner","Loser",
        # "WRank","LRank","WPts","LPts","W1","L1","W2","L2","W3","L3","W4","L4","W5","L5","Wsets","Lsets","Comment",
        # "B365W","B365L","EXW","EXL","LBW","LBL","PSW","PSL","SJW","SJL","MaxW","MaxL","AvgW","AvgL"
#       print "the cols are: ", cols
        # Since the input data includes double quotes we will strip them
        stripped_cols = map(lambda x: x[1:-1], cols)
        print "the stripped cols are: ", stripped_cols
        for line in csvFile:
            tuples = []
            nextLine = line.split(",")
            #nextLine = map(lambda x: x.encode("utf-8"), nextLineOrig)

            ts = datetime.strptime(nextLine[3][1:-1],'%m/%d/%Y')
            matchDateEpoch = (int)(ts.strftime('%s'))
            # Only process games involving Federer for now
            label = thePlayer + "_wins?"
            winner = nextLine[9][1:-1]
            loser = nextLine[10][1:-1]

            # only process Federer
            if not ( winner == thePlayer or loser == thePlayer):
                #print "!!!!not federer: nobody know nobody care!"
                continue

            if winner == thePlayer:
                tuples.append(["label", 1, ts])
                not_fed_stats = get_player_stats(allHistory, loser, matchDateEpoch)
                if not_fed_stats == None:
                    print "No stats for player ", loser
                else:
                    #print "loser stats for ", loser, ":", not_fed_stats
                    opp_prob_win = float(not_fed_stats['numWins'])/float(not_fed_stats['numGames'])
                    #print "Prob win for ", loser, ":", opp_prob_win
                    tuples.append(["OpponentProbWin",opp_prob_win,ts])
                    tuples.append(["OpponentRank", not_fed_stats['rank'],ts])
                    if not_fed_stats['numGamesVsFed'] != 0:
                        opp_prob_win_vs_fed = float(not_fed_stats['numWinsVsFed'])/float(not_fed_stats['numGamesVsFed'])
                        tuples.append(["OpponentProbWinVsFed",opp_prob_win_vs_fed,ts])

            else:
                #print "Federer is the loser - OMG! against ", winner
                tuples.append(["label", 0, ts])
                not_fed_stats = get_player_stats(allHistory, winner, matchDateEpoch)
                if not_fed_stats == None:
                    print "No stats for player ", winner
                else:
                    #print "winner stats for ", winner, ":", not_fed_stats
                    opp_prob_win = float(not_fed_stats['numWins'])/float(not_fed_stats['numGames'])
                    #print "Prob win for ", winner, ":", opp_prob_win
                    tuples.append(["OpponentProbWin",opp_prob_win,ts])
                    tuples.append(["OpponentRank", not_fed_stats['rank'],ts])
                    if not_fed_stats['numGamesVsFed'] != 0:
                        opp_prob_win_vs_fed = float(not_fed_stats['numWinsVsFed'])/float(not_fed_stats['numGamesVsFed'])
                        tuples.append(["OpponentProbWinVsFed",opp_prob_win_vs_fed,ts])

            # record a feature with the year so that we can train on the right subset
            #print "The year is ", ts.year
            tuples.append(["Year", ts.year, ts])
            tournament = nextLine[2][1:-1]
            tuples.append([stripped_cols[2], tournament, ts])
            round = nextLine[7][1:-1]
            tuples.append([stripped_cols[7], round, ts])
            for idx, val in enumerate(nextLine):
                # skip various columns that we don't want to see
                if idx in [0,2,7,3, 9,10]:
                    continue
                # From 2000 - 2004 there are two fewer columns
                if year < 2005:
                    if idx > 24 :
                        continue
                else:
                    if idx > 26:
                        continue
                nextVal = val;
                #print "idx = ", idx, " val ",  val[1:-1]
                if stripped_cols[idx] == "B365W" or stripped_cols[idx] == "B365L" :
                    print "weird and unexpected line: ", nextLine
                if val == "" or val == None :
                    nextVal = "NAN"
                #print "About to append to tuples ", stripped_cols[idx]
                tuples.append([stripped_cols[idx], nextVal, ts])


            num_lines += 1
            print "recording game ", num_lines
            #print "tournament = " , tournament
            #print "tuples:", tuples
            dataset.record_row("game_" + str(num_lines), tuples)

    dataset.commit()

"""
    mldb.log("request details:")
    mldb.log( "remainining   : " + remaining)
    print "verb          : ", verb
    print "resource      : ", resource
    print "restParams    : ", restParams, "length : ", len(restParams)
    print "payload       : ", payload
    print "contentType   : ", contentType
    print "contentLength : ", contentLength
    print "headers       : ", headers
    print "woohoo! The number of players is ", len(players)
    print "the number of tournaments is ", len(tournaments)
"""

def requestHandler(mldb, remaining, verb, resource, restParams, payload, contentType, contentLength, headers):
    playerNames = [];
    for key in players :
        playerNames.append(key);
#        print "player: ", key


    if remaining == "/players":
        return playerNames
    elif remaining == "/tournaments":
        print "returning tournaments "
        #mldb.log("returning tournaments")
        return tournaments
    else:
#        print "another route: ", remaining
        return "blah"
"""
    elif remaining == "/multiapply":
        print "multi apply we want to call our classifier block after calculating the right features"
        var result =  getAugmentedRestParams(restParams);
        var cls = result[0];
        var augmentedParams = result[1];
        // we expect to have a list of 4 parameters : The Opponent, The tournament, The round of the
        // tournament and the classifier. From that we construct a new set of parameters that we
        // can use to call the classifier
        // get the classifier
        var res = mldb.perform("GET", "/v1/blocks/classifyBlock"+ cls +"/apply", augmentedParams, "{}");
        print "explain block was called with result " , JSON.stringify(res));
        return res;
"""

mldb.plugin.set_request_handler(requestHandler);



def get_dataset(player):
#    global load_dataset
    # First try to load it
    datasetConfig = {
        "type": "mutable",
        "id": "tennis",
        "address": "tennis.beh.gz"
    };

    mldb.log("Deleting data set....")
    mldb.perform("DELETE", "/v1/datasets/tennis",[],"{}");
    mldb.log("dataset successfully deleted");

    dataset = mldb.create_dataset(datasetConfig);
    load_dataset(dataset, player);
    return dataset;

print ""
print ""
print "@@@@Running the tennis plugin@@@@@"
print "The time is now: " + str(datetime.now())

generate_stats_tables(tournaments, players)


print "Generated stats tables....load dataset"
trainingDataset = get_dataset(thePlayer)

#
# Create a classifier
#
train_classifier = True
if train_classifier:
    train_classifier_pipeline_config = {
        "id":"trainClsPipeline",
        "type":"classifier",
        "params":{
            "dataset":{"id":"tennis"},
            "algorithm":"glz",
            "classifierUri":"federer.cls",
            "where":"Year < 2014",
            "select":"* EXCLUDING(label, W1,L1,W2,L2,W3,L3,W4,L4,W5,L5,Wsets, Lsets, WPts, LPts, Year, LRank, WRank, Location)",
#                        "select":"* EXCLUDING label,W1",
            "label":"label = 1",
            "weight":"1.0"
            }
    }
    # for now always delete it...later we will be more careful
    del_res = mldb.perform("DELETE", "/v1/pipelines/federer_cls_train", [["sync","true"]], {})
    print "the result of the pipeline delete", del_res
    pipeline_output = mldb.perform("PUT","/v1/pipelines/federer_cls_train", [["sync","true"]], train_classifier_pipeline_config)
    print "pipeline output:", pipeline_output
    training_output = mldb.perform("PUT","/v1/pipelines/federer_cls_train/runs/1", [["sync","true"]], {"id":"1"})
    print "training output:", training_output

    block_config = {
        "id" : "classifyBlockglz",
        "type":"classifier.apply",
        "params":{"classifierUri":"federer.cls"}
        }
    del_res = mldb.perform("DELETE", "/v1/blocks/classifyBlockglz", [["sync","true"]], {})
    print "The result of the classifyBlockglz delete ", del_res
    block_output = mldb.perform("PUT","/v1/blocks/classifyBlockglz", [["sync","true"]], block_config)
    print "the block output ", block_output

test_classifier = True;
if test_classifier:
    with_clause = "(* EXCLUDING (label, W1, L1, W2, L2, W3, L3, W4, L4, W5, L5, Wsets, Lsets, WPts, LPts, Year, LRank, WRank, Location))"
#    with_clause = "(* EXCLUDING (label,W1))"
    score_clause = "APPLY BLOCK " + "classifyBlockglz" + " WITH " + with_clause + " EXTRACT (score)"
    print "the score clause is " , score_clause
    test_classifier_pipeline_config = {
        "id":"testClsPipeline",
        "type":"accuracy",
        "params": {
            "dataset": {"id":"tennis"},
            "output" : {
                "id":"cls_test_results",
                "type":"mutable",
                "address":"cls_test_results.beh.gz"
            },
            "where":"Year >= 2014",
            "score": score_clause,
            "label":"label = 1",
            "weight":"1.0"
         }
        }

    print "testing classifier"
    del_res = mldb.perform("DELETE", "/v1/pipelines/federer_cls_test", [["sync","true"]], {})
    print "The result of federer_cls_test delete ", del_res
    pipeline_output = mldb.perform("PUT","/v1/pipelines/federer_cls_test", [["sync", "true"]],
                                   test_classifier_pipeline_config)
    print "the test output ", pipeline_output

    del_res = mldb.perform("DELETE", "/v1/pipelines/federer_cls_test/runs/1", [["sync","true"]], {})
    print "the result of the delete run is ", del_res
    training_output = mldb.perform("PUT","/v1/pipelines/federer_cls_test/runs/1", [["sync", "true"]],
                                   {"id":"1"})
    print "the training output ", training_output

mldb.plugin.serve_static_folder("/static","static")
