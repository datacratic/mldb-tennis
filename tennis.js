

var players = {};// for each player we keep track of stats
var tournaments = {};//keep track of all tournaments
var allHistory = new Array();
var trainingYear = 2014;

//
// training history only records information up to the specified training year
// allHistory stores well..all the history
//
function generateStatsTables()
{
//    var history = new Array();// will store data for players at any given date
    var dataDir = "examples/tennis/data/";
    var year = 2000;
    var numLines = 0;
    plugin.log("generateStatsTables!");
    for( year = 2000 ; year < 2015; year++)
    {
	var fileToProcess = dataDir + "ATP_" + year.toString() + ".csv";

	var csvFile = mldb.openStream(fileToProcess);

	cols = csvFile.readLine().split(",");
	var prevDate = new Date();

	while(true) {
            var tuples = [];
            var nextLine;
            try {
		nextLine = csvFile.readLine().split(",");
            } catch (exc) {
		// end of file!
		break;
            }
	    numLines++;
	    var msec = Date.parse(nextLine[3]);
	    var matchDate = new Date(msec);

	    // Keep track of tournament information. For now we want the rounds that are specific to the
	    // tournament. i.e we want to know grand slams have more rounds for instance
	    var tournament = nextLine[2];
	    tournament = tournament.replace(/"/g,"");
	    var round = nextLine[7];
	    round = round.replace(/"/g,"");
	    var surface = nextLine[6];
	    surface = surface.replace(/"/g,"");
	    var court = nextLine[5];
	    court = court.replace(/"/g,"");
	    var bestof = nextLine[8];
	    bestof = bestof.replace(/"/g,"");
	    var series = nextLine[4];
	    series = bestof.replace(/"/g,"");

	    if (typeof tournaments[tournament] == 'undefined')
	    {
		tournaments[tournament] = {};
		tournaments[tournament]["rounds"] = [round];
		tournaments[tournament]["Surface"] = surface;
		tournaments[tournament]["Court"] = court;
		tournaments[tournament]["Best of"] = bestof;
		tournaments[tournament]["Series"] = series;
	    }
	    else
	    {
		// before adding make sure it is not already there
		if(tournaments[tournament]["rounds"].indexOf(round) == -1)
		    tournaments[tournament]["rounds"].push(round);
	    }
	    // if we change date that is when we record the state of the players at this point in time
	    if(matchDate.getTime() != prevDate.getTime())
	    {
		//
		// now we add these stats to the appropriate date entry
		// Note that if the date already exists then it is overwritten with more up to date stats
		// Since the source data is sorted by date at any given point in time we have the stats for
		// players at that point in time
		//
//		plugin.log(numLines, ":prev date ", prevDate, " matchDate ", matchDate);
		var playerSnapshot = JSON.parse(JSON.stringify(players));
		allHistory[msec] = playerSnapshot;
		prevDate = matchDate;
	    }
	    // We will have an associative array keyed by date. For each date we have a player and 
	    // associated stats as follows:
	    // # games numGames numWins numWinsVsFed
	    // These stats are a count that apply to all games prior to the date specified
	    var winner = nextLine[9];
	    winner = winner.replace(/"/g,"");
	    var loser = nextLine[10];
	    loser = loser.replace(/"/g,"");
	    var wrank = nextLine[11];
	    wrank = wrank.replace(/"/g,"");
	    var lrank = nextLine[12];
	    lrank = lrank.replace(/"/g,"");

	    // update general non-federer related stats
	    if (typeof players[loser] == 'undefined')
	    {
		//    plugin.log("First time we see this player", loser);
		var stats = { numGames: 1, numWins:0 , numGamesVsFed:0, numWinsVsFed:0, rank:lrank}
		players[loser] = stats;
	    }
	    else
	    {
		players[loser].numGames++;
		players[loser].rank = lrank;
	    }

	    if (typeof players[winner] == 'undefined')
	    {
		//	    plugin.log("and it is the first time we see this player", winner);
		var stats = { numGames: 1, numWins:1 , numGamesVsFed:0 , numWinsVsFed:0, rank:wrank}
		players[winner] = stats;
	    }
	    else
	    {
		players[winner].numGames++;
		players[winner].numWins++;
		players[winner].rank = wrank;
	    }
	    // now update federer specific stats
	    if(winner == "Federer R.")
	    {
		//	    plugin.log("Federer is winner against ", loser);
		players[loser].numGamesVsFed++;
	    }
	    else if(loser == "Federer R.")
	    {
		//	    plugin.log("federer loses to : " , winner);
		players[winner].numWinsVsFed++;
		players[winner].numGamesVsFed++;
		//	    plugin.log("and we have already seen this player", winner,":", JSON.stringify(players[winner]));
	    }
	}	
    }
/*
    plugin.log("Printing out all history information");
    for(theDate in allHistory)
    {
	var dateAsStr = new Date(Number(theDate));
	plugin.log("Player info @ ", dateAsStr.toJSON());
	for(player in allHistory[theDate])
	{
	    var currentPlayers = allHistory[theDate];
	    plugin.log("\t ",player, ":", JSON.stringify(currentPlayers[player])) ;
	}
    }
*/
    plugin.log("Processed ", numLines,  " lines. History generated!");
    plugin.log("Printing out tournament information:")
    for(tournament in tournaments)
    {
	plugin.log("Tournament: ", tournament);
	plugin.log("\t ", JSON.stringify(tournaments[tournament]));
    }
//    return history;
}

function getPlayerStats(history, player, ts)
{
    plugin.log("getPlayerStats for player:", player, " at time ", ts);
    var snapshot = history[ts];
    var playerStats = snapshot[player];
    return playerStats;
}

function stripQuotes(str)
{
    return str.replace(/"/g,"");    
}
function loadDataset(dataset)
{

    var dataDir = "examples/tennis/data/";
    var year = 2000;
    var num_lines = 0;

    for( year = 2000 ; year < 2015; year++)
    {
	var fileToProcess = dataDir + "ATP_" + year.toString() + ".csv";
	plugin.log("opening file ", fileToProcess); 
	var csvFile = mldb.openStream(fileToProcess);
	//    var csvFile = mldb.openStream("examples/tennis/data/ATP_2005-2014.csv");
	//    plugin.log("pwet pwet loaded file!");
	var thePlayer = "Federer R.";
	cols = csvFile.readLine().split(",");
	// cols are as follows
	// For the year from 2000 to 2004 (inclusive) there WPts and LPts are missing
	// "ATP","Location","Tournament","Date","Series","Court","Surface","Round","Best of","Winner","Loser",
	// "WRank","LRank","WPts","LPts","W1","L1","W2","L2","W3","L3","W4","L4","W5","L5","Wsets","Lsets","Comment",
	// "B365W","B365L","EXW","EXL","LBW","LBL","PSW","PSL","SJW","SJL","MaxW","MaxL","AvgW","AvgL"
	
	// Since the input data inclusdes double quotes we will strip them
	var strippedCols = cols.map(stripQuotes);
	plugin.log("original columns : ", cols, " with size " , cols.length);
	plugin.log("stripped columns : ", strippedCols, " with size " , strippedCols.length);
	while(true) {
	    var tuples = [];
            var nextLine;
            try {
		nextLine = csvFile.readLine().split(",");
            } catch (exc) {
		// end of file!
		break;
            }
	    //	plugin.log("timestamp = ", nextLine[3]);
	    //	plugin.log("converted = ", d);
	    //	plugin.log("match id: ", "match_" + num_lines);

	    // get the time stamp
	    var msec = Date.parse(nextLine[3]);
	    var ts = new Date(msec);
	    // only process games by Federer
	    var label = thePlayer + "_wins?";
	    var winner = nextLine[9];
	    winner = winner.replace(/"/g,"");
	    var loser = nextLine[10];
	    loser = loser.replace(/"/g,"");
	    // only process Federer
	    if( !(winner == thePlayer || loser == thePlayer))
	    {
		//	    plugin.log("not federer: nobody know nobody care!");
		continue;
	    }
	    var notFedStats;
	    if(winner == thePlayer)
	    {
		tuples.push(["label", 1, ts]);		
		notFedStats = getPlayerStats(allHistory, loser, msec);
		plugin.log(label , 1, " against " , loser, " with stats : " , JSON.stringify(notFedStats));
		if(notFedStats == undefined)
		    plugin.log("no stats for player:", loser);
		else
		{
		    // add stats for Fed's opponent
		    plugin.log("Prob win for ", loser, ":", notFedStats.numWins/notFedStats.numGames);
		    var oppProbWin = notFedStats.numWins/notFedStats.numGames ;
		    tuples.push(["OpponentProbWin", oppProbWin, ts]);
		    tuples.push(["OpponentRank", notFedStats.rank, ts]);
		    if(notFedStats.numGamesVsFed != 0)
		    {
			plugin.log("Prob win against Federer for ", loser, ":", notFedStats.numWinsVsFed/notFedStats.numGamesVsFed);
			tuples.push(["OpponentProbWinVsFed", notFedStats.numWinsVsFed/notFedStats.numGamesVsFed, ts]);
		    }
		}
	    }
	    if(loser == thePlayer)
	    {
		tuples.push(["label", 0, ts]);
		notFedStats = getPlayerStats(allHistory, winner, msec);
		plugin.log(label, 0, " loses to ", winner, " with stats : " , JSON.stringify(notFedStats));
		if(notFedStats == undefined)
		    plugin.log("no stats for player:", winner);
		else
		{
		    // add stats for Fed's opponent
		    plugin.log("Prob win for ", winner, ":", notFedStats.numWins/notFedStats.numGames);
		    var oppProbWin = notFedStats.numWins/notFedStats.numGames ;
		    tuples.push(["OpponentProbWin", oppProbWin, ts]);
		    tuples.push(["OpponentRank", notFedStats.rank, ts]);
		    if(notFedStats.numGamesVsFed != 0)
		    {
			plugin.log("Prob win against Federer for ", winner, ":", notFedStats.numWinsVsFed/notFedStats.numGamesVsFed);
			tuples.push(["OpponentProbWinVsFed", notFedStats.numWinsVsFed/notFedStats.numGamesVsFed, ts]);
		    }
		}
	    }
	    // Record a feature with the year so we can easily select the right times
	    tuples.push(["Year", ts.getFullYear(), ts]);

	    var tournament = nextLine[2];
	    tournament = tournament.replace(/"/g,"");
	    tuples.push([strippedCols[2], tournament, ts]);
	    var round = nextLine[7];
	    round = round.replace(/"/g,"");
	    tuples.push([strippedCols[7], round, ts]);

            for(var i in nextLine) {
		// we skip the first column
		if(i==0) continue;
		// we skip the tournament since we add it above without double quotes around it
		if(i==2) continue;
		// we skip the round since we add it above without double quotes
		if(i==7) continue;
		// we skip the timestamp
		if(i==3) continue;
		// column 10 is the winner
		if(i==9) continue
		// column 11 is the loser
		if(i==10) continue;
		// This is because from 2000-2004 there are two fewer columns
		if(year < 2005)
		{
		    if(i > 24) continue;
		}
		else
		    if(i>26) continue;

		//plugin.log("val: '"+nextLine[i]+"'");
		nextVal = nextLine[i]
		if(strippedCols[i] == "B365W" || strippedCols[i] == "B365L")
		    plugin.log("Weird line: ", nextLine);
		if(nextVal == '' || nextVal === undefined)
                    nextVal = "NAN";
//		plugin.log(["num vals : ", nextLine.length, i,  cols[i], nextVal, ts]);
		tuples.push([strippedCols[i], nextVal, ts]);
            }
            plugin.log(tuples);
            num_lines++;
	    try {
		dataset.recordRow("game_" + num_lines.toString(), tuples);
	    }
	    catch(exc)
	    {
		plugin.log("invalid line ", nextLine); 
	    }
            //if(num_lines>15) break;
	}
    }
    plugin.log("recorded " + num_lines + " games");
    dataset.commit();
}

function getAugmentedRestParams(restParams)
{
    // validates the input and returns new parameters with which we can call the 
    // classifier block
    var augmentedRestParams = [];
    var cls ;
    if(restParams.length != 4)
	throw new Error("Insufficient number of parameters");
    //
    // so now we now we have the number of parameters that we need to 
    // check that they are the right ones and that we know what they are
    //
    for(var i = 0; i < restParams.length ;++i)
    {
	if(restParams[i].length != 2)
	    throw new Error("missing key value pair for parameter " + (i+1).toString());
	var key = restParams[i][0];
	var value = restParams[i][1].trim();
	plugin.log("i = ", i , " param= ", key, ":<", value, ">");
	if(key == "Opponent")
	{
	    plugin.log("check if we know player : ", value);
	    // check if we have info on this player
	    if (typeof players[value] == 'undefined')	    
	    {
		throw new Error("Unknown key value pair for " + key + ":" + value);
	    }
	    else
	    {
		plugin.log("we have info about player ", value, " stats ", JSON.stringify(players[value]));
		var probWin = players[value].numWins/players[value].numGames;
		var probWinVsFed = players[value].numWinsVsFed/players[value].numGamesVsFed ;
		plugin.log(" Probability of win ", probWin, " prob win vs Fed ", probWinVsFed);
		augmentedRestParams.push(["OpponentProbWin",probWin]);
		augmentedRestParams.push(["OpponentProbWinVsFed",probWinVsFed]);
		augmentedRestParams.push(["OpponentRank", players[value].rank]);
	    }
	}
	else if(key == "Tournament")
	{
	    plugin.log("check if we know tournament : ", value);
	    // check if we have info on this player
	    if (typeof tournaments[value] == 'undefined')	    
		throw new Error("Unknown key value pair for " + key + ":" + value);
	    else
	    {
		plugin.log("we have info about tournaments ", value, " stats ", 
			   JSON.stringify(tournaments[value]));

		augmentedRestParams.push(["Tournament", value]);
		augmentedRestParams.push(["Surface",tournaments[value]["Surface"]]);
		augmentedRestParams.push(["Court",tournaments[value]["Court"]]);
	        augmentedRestParams.push(["Best of",tournaments[value]["Best of"]]);
	        augmentedRestParams.push(["Series",tournaments[value]["Series"]]);
	    }
	}
	else if(key == "Round")
	{
	    plugin.log("we have round ", value );
	    augmentedRestParams.push(["Round", value]);
	}
	else if(key == "Classifier")
	{
	    cls = value;
	}
    }

    plugin.log("the classifier is ", cls);
    plugin.log("REST Params : ", augmentedRestParams);
    return [cls,augmentedRestParams];
}

function requestHandler(remaining, verb, resource, restParams, payload, contentType, contentLength, headers)
{
    plugin.log("request details:");
    plugin.log("remainining   : ", remaining);
    plugin.log("verb          : ", verb);
    plugin.log("resource      : ", resource);
    plugin.log("restParams    : ", restParams, "length : ", restParams.length );
    plugin.log("payload       : ", payload);
    plugin.log("contentType   : ", contentType);
    plugin.log("contentLength : ", contentLength);
    plugin.log("headers       : ", headers);
    plugin.log("woohoo! The number of players is ", Object.keys(players).length);
    plugin.log("the number of tournaments is ", Object.keys(tournaments).length);
    var playerNames = [];
    for (var key in players) {
	playerNames.push(key);
//	plugin.log("player: ", key);
    }

    if(remaining == "/players")
	return playerNames;
    else if(remaining == "/tournaments")
    {
	plugin.log("returning tournaments");
	return tournaments;
    }
    else if(remaining == "/multiapply")
    {
	plugin.log("multi apply we want to call our classifier block after calculating the right features");
	var result =  getAugmentedRestParams(restParams);
	var cls = result[0];
	var augmentedParams = result[1];
	// we expect to have a list of 4 parameters : The Opponent, The tournament, The round of the
	// tournament and the classifier. From that we construct a new set of parameters that we
	// can use to call the classifier
	// get the classifier
	var res = mldb.perform("GET", "/v1/blocks/classifyBlock"+ cls +"/apply", augmentedParams, "{}");
	plugin.log("explain block was called with result " , JSON.stringify(res));
	return res;
    }
}

plugin.setRequestHandler(requestHandler);

function getDataset()
{
    // First try to load it
    var datasetConfig = {
        type: "beh",
        id: "tennis",
        address: "tennis.beh.gz"
    };

//     try {
//         plugin.log("creating dataset with config", JSON.stringify(datasetConfig));
//         return mldb.createDataset(datasetConfig);
//     } catch (exc) {
//         plugin.log("couldn't load dataset; creating:", JSON.stringify(exc));
//         // Delete this dataset (it doesn't delete the underlying file), and create another
    plugin.log("Deleting data set....");
    mldb.perform("DELETE", "/v1/datasets/tennis");
//     }

    datasetConfig.type = "mutable";
    var dataset = mldb.createDataset(datasetConfig);
    loadDataset(dataset);
    return dataset;
}


//plugin.serveStaticFolder("/static", "examples/tennis/static");

generateStatsTables();

var trainingDataset = getDataset();

var status = trainingDataset.status();
plugin.log("training dataset status", JSON.stringify(status));

// Create a SVD pipeline
var trainSvd = false;
if(trainSvd)
{
    var svdConfig = {
	type : "svd",
	params : {
	    dataset: {"id": "tennis"}
	}
    };

    var svdOutput = mldb.perform("PUT", "/v1/pipelines/tennis_svd",[["sync","true"]], JSON.stringify(svdConfig));
}

// now create a classifier
var trainClassifier = true;

if (trainClassifier) {  
    var trainClassifierPipelineConfig = {
        id: "trainClassifierPipeline",
        type: "classifier",
        params: {
            dataset: { id: "tennis" },
            algorithm: "glz",
            classifierUri: "federer.cls",
            where: "Year < 2014",
//            select: "OpponentProbWin,OpponentProbWinVsFed,OpponentRank",
            select: "* EXCLUDING(label, W1,L1,W2,L2,W3,L3,W4,L4,W5,L5,Wsets, Lsets, WPts, LPts, Year, LRank, WRank, Location)",
            label: "label = 1",
            weight: "1.0"
        }
    };

    var pipelineOutput = mldb.perform("PUT", "/v1/pipelines/federer_cls_train", [["sync", "true"]],
                                      JSON.stringify(trainClassifierPipelineConfig));

    plugin.log("pipeline output", JSON.stringify(pipelineOutput));

    var trainingOutput = mldb.perform("PUT", "/v1/pipelines/federer_cls_train/trainings/1",
                                      [["sync", "true"]], "{}");

    plugin.log("training output", JSON.stringify(trainingOutput));

    // now create a block that
    var blockConfig = {
	id: "classifyBlockglz",
        type: "classifier.apply",
        params: {
            classifierUri: "federer.cls"
        }
    };

    var blockOutput = mldb.perform("PUT", "/v1/blocks/classifyBlockglz", [["sync", "true"]], 
				   JSON.stringify(blockConfig));
    plugin.log("About to stringify block output");
    plugin.log("blockoutp", JSON.stringify(blockOutput));
    plugin.log("block output stringified ");
}

var testClassifier = true;

if (testClassifier) {
    var blockConfig = {
        id: "testClassifierBlock",
        type: "classifier.apply",
        params: {
            classifierUri: "federer.cls"
        }
    };

    var testClassifierPipelineConfig = {
        id: "testClassifierPipeline",
        type: "accuracy",
        params: {
            dataset: { id: "tennis" },
            output: { id: "cls_test_results", type: "mutable", address: "cls_test_results.beh.gz" },
            block: blockConfig,
	    "with": "* EXCLUDING (label, W1, L1, W2, L2, W3, L3, W4, L4, W5, L5, Wsets, Lsets, WPts, LPts, Year, LRank, WRank, Location)",
	    where: "Year >= 2014",
            score: "score",
            label: "label = 1",
            weight: "1.0"
        }
    };

    plugin.log("testing classifier....");
    var pipelineOutput = mldb.perform("PUT", "/v1/pipelines/federer_cls_test", [["sync", "true"]],
                                      JSON.stringify(testClassifierPipelineConfig));

    plugin.log("pipeline output", JSON.stringify(pipelineOutput));

    var trainingOutput = mldb.perform("PUT", "/v1/pipelines/federer_cls_test/trainings/1",
                                      [["sync", "true"]], "{}");

    plugin.log("training output", JSON.stringify(trainingOutput));
}

plugin.serveStaticFolder("/static", "examples/tennis/static/");

// The output of the last line of the script is returned as the result of the script,
// just like in Javscript eval
"success!"

