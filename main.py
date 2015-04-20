import os,socket,time,csv,json,datetime
from datetime import datetime
from copy import deepcopy
import json


tournaments = {}
players ={}
playerNames = []
tournamentsToReturn = {} # we only return those masters level and grand slams for now
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

    print "Generating stats tables...."
    dataDir = mldb.plugin.get_plugin_dir() + "/data/"
    print "the data directory is " + dataDir

#   year = 2000
    numLines = 0
    prevDate = int(datetime.now().strftime('%s'))
    for year in range(2000,2015):
        # we do not process 2007 because ATP data actually contains WTA matches
        if year == 2007:
            continue
        print "The year is :" + str(year)
        fileToProcess = dataDir + "ATP_" + str(year) + ".csv"
        print "The file to process is " + fileToProcess
        
        csvFile = open(fileToProcess, 'r')
        firstLine = csvFile.readline()
        print "the first line is :" + firstLine
        for line in csvFile:
            #print line
            nextLine = line.split(",")
            # we seem to have some WTA stats in some of the files. Filter them
            if nextLine[4] == '"SEC"':
                mldb.log("!!!!!!Found WTA data in ATP files: " + line)
                continue
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
                if series == "Masters" or series == "Grand Slam":
                    tournamentsToReturn[tournament] = {}
                    tournamentsToReturn[tournament]["rounds"] = {round:True}
                    tournamentsToReturn[tournament]["Surface"] = surface;
                    tournamentsToReturn[tournament]["Court"] = court;
                    tournamentsToReturn[tournament]["Best of"] = bestof;
                    tournamentsToReturn[tournament]["Series"] = series;
                    
            else:
                # before adding a round make sure that it is not already there
                if not round in tournaments[tournament]["rounds"]:
                    #print "Adding round ", round , " to tournament ", tournament
                    tournaments[tournament]["rounds"][round] = True
                    if series == "Masters" or series == "Grand Slam":
                        tournamentsToReturn[tournament]["rounds"][round] = True
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

            winner = nextLine[9][1:-1].rstrip()
            loser = nextLine[10][1:-1].rstrip()
            wrank = nextLine[11][1:-1]
            lrank = nextLine[12][1:-1]

            try:
                lrank = int(lrank)
            except ValueError:
                mldb.log("Failed to convert to int " + line + " : lrank<" + lrank + ">")
                lrank = 0

            try:
                wrank = int(wrank)
            except ValueError:
                mldb.log("Failed to convert to int " + line + " : wrank<" + wrank + ">")
                wrank = 0
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

    # we are only going to return players that were ranked in the top 30 at the end of 2014
    # and who have played at least one game versus Federer
    for key in players :
        if key != thePlayer and players[key]["rank"] <= 30 and players[key]["rank"] > 0 and players[key]["numGames"] > 10 and players[key]["numGamesVsFed"] > 0:
            mldb.log("Player " + key + ":" + json.dumps(players[key]))
            playerNames.append(key);

    mldb.log("The number of players is " + str(len(playerNames)))        
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
    dataDir = mldb.plugin.get_plugin_dir() + "/data/"
    year = 2000
    num_lines = 0

    for year in range(2000,2015):
        # we do not process 2007 because ATP data actually contains WTA matches
        if year == 2007:
            continue

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
            if nextLine[4] == '"SEC"':
                mldb.log("!!!!!!Found WTA data in ATP files: " + line)
                continue
            ts = datetime.strptime(nextLine[3][1:-1],'%m/%d/%Y')
            matchDateEpoch = (int)(ts.strftime('%s'))
            # Only process games involving Federer for now
            label = thePlayer + "_wins?"
            winner = nextLine[9][1:-1].rstrip()
            loser = nextLine[10][1:-1].strip()

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
                    tuples.append(["OpponentProbWin", opp_prob_win, ts])
                    if not_fed_stats['rank'] != 0:
                        tuples.append(["OpponentRank", not_fed_stats['rank'], ts])
                    if not_fed_stats['numGamesVsFed'] != 0:
                        opp_prob_win_vs_fed = float(not_fed_stats['numWinsVsFed'])/float(not_fed_stats['numGamesVsFed'])
                        tuples.append(["OpponentProbWinVsFed", opp_prob_win_vs_fed, ts])

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
                    tuples.append(["OpponentProbWin", opp_prob_win, ts])
                    if not_fed_stats['rank'] != 0:
                        tuples.append(["OpponentRank", not_fed_stats['rank'],ts])
                    if not_fed_stats['numGamesVsFed'] != 0:
                        opp_prob_win_vs_fed = float(not_fed_stats['numWinsVsFed'])/float(not_fed_stats['numGamesVsFed'])
                        tuples.append(["OpponentProbWinVsFed", opp_prob_win_vs_fed, ts])

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


def getAugmentedRestParams(mldb,restParams):
    # validates the input and returns new parameters with which we can call the 
    # classifier block
    cls = ""
    augmented_rest_params = []
    augmented_rest_params.append(["encoding","json"])
    if len(restParams) != 4:
        raise Exception("Insufficient number of parameters")

    mldb.log("we have the right number of parameters")
    for param in restParams:
        key = param[0]
        value = param[1].strip()
        mldb.log("key = " + key + " value = " + value)
        if key == "Opponent":
            mldb.log("Checking if know oppponent " + key)
            opp_stats = players.get(value)
            if opp_stats == None:            
                raise Exception("Failed to find player " + value)
            else:
                mldb.log("We have info about player " + value + " stats :" + json.dumps(opp_stats))
                opp_prob_win = float(opp_stats['numWins'])/float(opp_stats['numGames'])
                opp_prob_win_vs_fed = float(opp_stats['numWinsVsFed'])/float(opp_stats['numGamesVsFed'])
                augmented_rest_params.append(["OpponentProbWin", str(opp_prob_win)])
                augmented_rest_params.append(["OpponentProbWinVsFed", str(opp_prob_win_vs_fed)])
                if opp_stats['rank'] != 0:
                    augmented_rest_params.append(["OpponentRank", str(opp_stats['rank'])])
        elif key == "Tournament":
            mldb.log("Checking if know tournament " + key)
            tournament_stats = tournaments.get(value)
            if tournament_stats == None:            
                raise Exception("Failed to find tournament " + value)
            else:
                mldb.log("We have info about tournament " + value + " stats :" + json.dumps(tournament_stats))
                augmented_rest_params.append(["Tournament", '"' + value + '"'])
                augmented_rest_params.append(["Surface", '"' + tournament_stats['Surface'] + '"'])
                augmented_rest_params.append(["Court", '"' + tournament_stats['Court'] + '"'])
                augmented_rest_params.append(["Best of", '"' + tournament_stats['Best of'] + '"'])
                augmented_rest_params.append(["Series", '"' + tournament_stats['Series'] + '"'])
        elif key == "Round":
            mldb.log("We have info about round " + value)
            augmented_rest_params.append(["Round", '"' + value + '"'])
        elif key == "Classifier":
            cls = value
        else:
            raise Exception("Unknown key in rest parameters " + value)
        print "the cls is ", cls

    return (cls, augmented_rest_params)

def requestHandler(mldb, remaining, verb, resource, restParams, payload, contentType, contentLength, headers):
    mldb.log("request details:")
    mldb.log( "remainining   : " + str(remaining))
    mldb.log("verb          : " + str(verb))
    mldb.log("resource      : " + str(resource))
    mldb.log("restParams    : " +  str(restParams) +  "length : " + str(len(restParams)))
    mldb.log("payload       : " + str(payload))
    mldb.log("contentType   : " + str(contentType))
    mldb.log("contentLength : " + str(contentLength))
#    mldb.log("headers       : " + json.dumps(headers))
    mldb.log("The number of players is " + str(len(playerNames)))
    mldb.log("the number of tournaments is " + str(len(tournamentsToReturn)))

    
    if remaining == "/players":
        return playerNames
    elif remaining == "/tournaments":
        mldb.log("returning tournaments")
        return tournamentsToReturn
    elif remaining == "/multiapply":
        mldb.log("multi apply we want to call our classifier block after calculating the right features")
        cls, augmented_params =  getAugmentedRestParams(mldb, restParams)
        mldb.log("augmented_params:" + str(augmented_params))
        mldb.log("the classifier to use is " + cls)
        res = mldb.perform("GET", "/v1/blocks/probabilizer_prod"+ cls +"/application", augmented_params, "{}")
        mldb.log("the result of the probabilizer " + json.dumps(res))

        # now also want to call the explain block
        expl_res = mldb.perform("GET", "/v1/blocks/explainBlockProd"+ cls +"/application", augmented_params, "{}")
        mldb.log("Result of explain block : " + json.dumps(expl_res))
        combined_results = {}
        combined_results["results"] = [res, expl_res]
        mldb.log("combined result : " + json.dumps(combined_results))
        return combined_results


def get_dataset(player):
#    global load_dataset
    # First try to load it
    datasetConfig = {
        "type": "mutable",
        "id": "tennis",
        "params": { "artifactUri": "file:///var/mldb/tennis.beh.gz"}
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
mldb.plugin.set_request_handler(requestHandler)
print "Generated stats tables....load dataset"
trainingDataset = get_dataset(thePlayer)

#
# Create a classifier
#
train_classifier = True
cls_algos = ["glz", "dt","bbdt"]
# clean up in case things are already created
def delete_entity(entity):
    mldb.log("Deleting entity< " + entity + ">")
    res = mldb.perform("DELETE", entity, [], {})
    mldb.log("...with result : " +json.dumps(res))

for cls_algo in cls_algos:
    print "cleaning up algo ", cls_algo
    delete_entity("/v1/pipelines/federer_cls_train_%s" % cls_algo)
    delete_entity("/v1/pipelines/federer_cls_prod_%s" % cls_algo)
    delete_entity("/v1/blocks/classifyBlock%s" % cls_algo)
    delete_entity("/v1/blocks/classifyBlockProd%s" % cls_algo)
    delete_entity("/v1/pipelines/federer_prob_train_%s" % cls_algo )
    delete_entity("/v1/pipelines/federer_prob_prod_%s" % cls_algo )
    delete_entity("/v1/blocks/apply_probabilizer%s" % cls_algo)
    delete_entity("/v1/blocks/apply_probabilizer_prod%s" % cls_algo)
    delete_entity("/v1/blocks/probabilizer%s" % cls_algo)
    delete_entity("/v1/blocks/probabilizer_prod%s" % cls_algo)
    print "clean up completed"

if train_classifier:
    for cls_algo in cls_algos:
        train_classifier_pipeline_config = {
            "id":"federer_cls_train_" + cls_algo,
            "type":"classifier",
            "params":{
                "dataset":{"id":"tennis"},
                "algorithm":cls_algo,
                "classifierUri":"federer_%s.cls" % cls_algo,
                "where":"Year < 2014 AND rowHash() != 1",
                "select":"* EXCLUDING(label, W1,L1,W2,L2,W3,L3,W4,L4,W5,L5,Wsets, Lsets, WPts, LPts, Year, LRank, WRank, Location)",
                #                        "select":"* EXCLUDING label,W1",
                "label":"label = 1",
                "weight":"1.0"
                }
            }
        pipeline_output = mldb.perform("PUT","/v1/pipelines/federer_cls_train_" + cls_algo, [], 
                                       train_classifier_pipeline_config)
        mldb.log("pipeline output:" +json.dumps(pipeline_output))
        training_output = mldb.perform("PUT","/v1/pipelines/federer_cls_train_%s/runs/1" % cls_algo, [], 
                                       {})
        mldb.log("training output:" + json.dumps(training_output))
        
        block_config = {
            "id" : "classifyBlock" + cls_algo,
            "type":"classifier.apply",
            "params":{"classifierUri":"federer_%s.cls" % cls_algo}
            }
        block_output = mldb.perform("PUT","/v1/blocks/classifyBlock%s" % cls_algo, [], block_config)
        mldb.log("the block output " + json.dumps(block_output))
        
        with_clause = "(* EXCLUDING (label, W1, L1, W2, L2, W3, L3, W4, L4, W5, L5, Wsets, Lsets, WPts, LPts, Year, LRank, WRank, Location))"
        score_clause = "APPLY BLOCK " + "classifyBlock" + cls_algo + " WITH " + with_clause + " EXTRACT (score)"
        # Now add the probabilizer
        train_probabilizer_pipeline_config = {
            "id":"federer_prob_train_%s" % cls_algo,
            "type":"probabilizer",
            "params":{
                "dataset":{"id":"tennis"},
                "probabilizerUri":"probabilizer" + cls_algo +".json",
                "where":"Year < 2014 AND rowHash() % 5 = 1",
                "select":score_clause,
                "label":"label = 1"
                }
            }
        
        print mldb.perform("PUT", "/v1/pipelines/federer_prob_train_%s" % cls_algo, 
                           [], 
                           train_probabilizer_pipeline_config)
        
        
        train_probabilizer_result = mldb.perform("PUT", "/v1/pipelines/federer_prob_train_%s/runs/1" % cls_algo,
                                                 [], 
                                                 {})
        
        
        probabilizer_block_config = {
            "id":"probabilizer" + cls_algo,
            "type":"serial",
            "params":{
                "steps":[
                    {
                        "id":"classifyBlock" + cls_algo
                        },
                    {
                        "id":"apply_probabilizer" + cls_algo,
                        "type":"probabilizer.apply",
                        "params": {
                            "probabilizerUri":"probabilizer" + cls_algo +".json"
                            }
                        }
                    ]
                }
            }
        
        probabilizer_block_output = mldb.perform("PUT", "/v1/blocks/" +probabilizer_block_config["id"],
                                                 [], 
                                                 probabilizer_block_config)
        mldb.log("The result of the probabilizer block config" +json.dumps(probabilizer_block_output))

        # add an explain block
        expl_block_config = {
            "id":"explainBlock" + cls_algo,
            "type":"classifier.explain",
            "params": {
                "classifierUri":"federer_%s.cls" % cls_algo
                }
            }
        delete_entity("/v1/blocks/explainBlock%s" % cls_algo)
        explain_block_output = mldb.perform("PUT", "/v1/blocks/explainBlock%s" % cls_algo, [], expl_block_config)
        mldb.log(cls_algo + ":result of the explain block " + json.dumps(explain_block_output))


# Train a classifier with all the data for production
train_prod_classifier = True
if train_prod_classifier:
    for cls_algo in cls_algos:
        prod_classifier_pipeline_config = {
            "id":"federer_cls_prod_" + cls_algo,
            "type":"classifier",
            "params":{
                "dataset":{"id":"tennis"},
                "algorithm":cls_algo,
                "classifierUri":"federer_prod%s.cls" % cls_algo,
                "where":"rowHash() != 1",
                "select":"* EXCLUDING(label, W1,L1,W2,L2,W3,L3,W4,L4,W5,L5,Wsets, Lsets, WPts, LPts, Year, LRank, WRank, Location)",
                #                        "select":"* EXCLUDING label,W1",
                "label":"label = 1",
                "weight":"1.0"
                }
            }
        pipeline_prod_output = mldb.perform("PUT","/v1/pipelines/federer_cls_prod_" + cls_algo, [], 
                                            prod_classifier_pipeline_config)
        mldb.log("!!! prod pipeline output:" +json.dumps(pipeline_prod_output))
        training_output = mldb.perform("PUT","/v1/pipelines/federer_cls_prod_%s/runs/1" % cls_algo, [], 
                                       {})
        mldb.log("prod output:" + json.dumps(training_output))

        block_config_prod = {
            "id" : "classifyBlockProd" + cls_algo,
            "type":"classifier.apply",
            "params":{"classifierUri":"federer_prod%s.cls" % cls_algo}
            }
        block_output_prod = mldb.perform("PUT","/v1/blocks/classifyBlockProd%s" % cls_algo, 
                                         [], block_config_prod)
        mldb.log("!!!!the prod block output " + json.dumps(block_output_prod))

        with_clause = "(* EXCLUDING (label, W1, L1, W2, L2, W3, L3, W4, L4, W5, L5, Wsets, Lsets, WPts, LPts, Year, LRank, WRank, Location))"
        score_clause = "APPLY BLOCK " + "classifyBlockProd" + cls_algo + " WITH " + with_clause + " EXTRACT (score)"
        # Now add the probabilizer
        prod_probabilizer_pipeline_config = {
            "id":"federer_prob_prod_%s" % cls_algo,
            "type":"probabilizer",
            "params":{
                "dataset":{"id":"tennis"},
                "probabilizerUri":"probabilizer_prod" + cls_algo +".json",
                "where":"rowHash() % 5 = 1",
                "select":score_clause,
                "label":"label = 1"
                }
            }
        
        print mldb.perform("PUT", "/v1/pipelines/federer_prob_prod_%s" % cls_algo, 
                           [], 
                           prod_probabilizer_pipeline_config)
        
        
        prod_probabilizer_result = mldb.perform("PUT", "/v1/pipelines/federer_prob_prod_%s/runs/1" % cls_algo,
                                                 [], 
                                                 {})
        
        
        probabilizer_prod_block_config = {
            "id":"probabilizer_prod" + cls_algo,
            "type":"serial",
            "params":{
                "steps":[
                    {
                        "id":"classifyBlockProd" + cls_algo
                        },
                    {
                        "id":"apply_probabilizer_prod" + cls_algo,
                        "type":"probabilizer.apply",
                        "params": {
                            "probabilizerUri":"probabilizer_prod" + cls_algo +".json"
                            }
                        }
                    ]
                }
            }
        
        probabilizer_prod_block_output = mldb.perform("PUT", "/v1/blocks/" +probabilizer_prod_block_config["id"],
                                                      [], 
                                                      probabilizer_prod_block_config)
        mldb.log("!!!(PROD)The result of the probabilizer block config" +json.dumps(probabilizer_prod_block_output))
        # add an explain block
        expl_prod_block_config = {
            "id":"explainBlockProd" + cls_algo,
            "type":"classifier.explain",
            "params": {
                "classifierUri":"federer_prod%s.cls" % cls_algo
                }
            }
        delete_entity("/v1/blocks/explainBlockProd%s" % cls_algo)
        explain_prod_block_output = mldb.perform("PUT", "/v1/blocks/explainBlockProd%s" % cls_algo, [], 
                                            expl_prod_block_config)
        mldb.log(cls_algo + ":result of the explain block(PROD)" + json.dumps(explain_prod_block_output))


test_classifier = False;
if test_classifier:
    for cls_algo in cls_algos:
        with_clause = "(* EXCLUDING (label, W1, L1, W2, L2, W3, L3, W4, L4, W5, L5, Wsets, Lsets, WPts, LPts, Year, LRank, WRank, Location))"
    #    with_clause = "(* EXCLUDING (label,W1))"
        print "the score clause is " , score_clause
        test_classifier_pipeline_config = {
            "id":"federer_cls_test_%s" % cls_algo,
            "type":"accuracy",
            "params": {
                "dataset": {"id":"tennis"},
                "output" : {
                    "id":"cls_test_results_%s" % cls_algo,
                    "type":"mutable",
                    "params": { "artifactUri":"file:///var/mldb/cls_test_results_%s.beh.gz" % cls_algo}
                    },
                "where":"Year >= 2014",
                "score": score_clause,
                "label":"label = 1",
                "weight":"1.0"
                }
            }

        mldb.log( "testing classifier")
        delete_entity("/v1/pipelines/federer_cls_test_%s" % cls_algo)
        pipeline_output = mldb.perform("PUT","/v1/pipelines/federer_cls_test_%s" % cls_algo, [],
                                   test_classifier_pipeline_config)
        mldb.log(cls_algo + ": test config output " + json.dumps(pipeline_output))

        delete_entity("/v1/pipelines/federer_cls_test_%s/runs/1" % cls_algo)
        training_output = mldb.perform("PUT","/v1/pipelines/federer_cls_test_%s/runs/1" % cls_algo, 
                                       [],
                                       {"id":"1"})
        mldb.log(cls_algo + ":test training output " + json.dumps(training_output))

mldb.plugin.serve_static_folder("/static","static")
mldb.plugin.serve_documentation_folder('doc')
