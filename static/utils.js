function update() {
    var theUrl = "../multiapply?" + $("#oddsForm").serialize();
    $("#urlCalled").text(theUrl);
     $.ajax({
       url: theUrl,
       dataType: "json",
       error: function (jqXHR, textStatus, errorThrown) {
           alert(jqXHR.status + textStatus);
       },
       success: function(data) {
           var theResponse = JSON.parse(data.results[0].response);
           var prob = parseFloat(theResponse.pins.prob) * 100;
           var theExpl = JSON.parse(data.results[1].response);
           var oppExpl="";
           var tournamentExpl="";
           var roundExpl="";
           for(var feature in theExpl.pins) {
               if( feature == "expl:OpponentProbWin" || 
                   feature == "expl:OpponentProbWinVsFed" || feature == "expl:OpponentRank")
               {
                   oppExpl = oppExpl + "(" + feature.substr(5) + ":" + theExpl.pins[feature] + ")"
               }
               else if ( feature == "expl:Tournament" || feature == "expl:Surface" ||
                         feature == "expl:Court" || feature == "expl:Best of" || 
                         feature == "expl:Series")
               {
                   tournamentExpl = tournamentExpl + "(" + feature.substr(5) + ":" + theExpl.pins[feature] + ")"
               }
               else if( feature == "expl:Round")
               {
                   roundExpl = roundExpl + "(" + feature.substr(5) + ":" + theExpl.pins[feature] + ")"
               }
           }
           $("#explainOpponent").text(oppExpl);
           $("#explainTournament").text(tournamentExpl);
           $("#explainRound").text(roundExpl);
           $('.progress-bar').css('width', prob+'%').attr('aria-valuenow', prob);
           $('.progress-bar').text(prob.toFixed(2)+"%");
       }
   });
};

$(function() {
  $.when(
      $.getJSON("../tournaments"), 
      $.getJSON("../players")
  )
  .then(function(tournamentsRes, playersRes){
    var tournaments = tournamentsRes[0];
    var players = playersRes[0];
    players.sort();

    $("#inputOpponent").append(players.map(function(p){
      return $("<option>", {value:p}).text(p);
    }));

    function updateRounds(){
        var priorRound = $("#inputRound").val();
        var rounds = tournaments[$("#inputTournament").val()].rounds;
        $("#inputRound").empty().append($.map(rounds, function(rval, rkey){
            var result = $("<option>", {value: rkey}).text(rkey);
            if(rkey == priorRound) result.attr('selected', 'selected');
            return result;
        }));
        $("#inputRound").select(priorRound);
    };

    $("#inputTournament").append($.map(tournaments, function(tval, tkey){
      return $("<option>", {value:tkey}).text(tkey);
    }))
    .on("change", updateRounds);

    updateRounds();
    update();
    $("form :input").change(update);
  });
    
});
