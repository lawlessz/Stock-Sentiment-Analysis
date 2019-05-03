var app = require('express')();
var http = require('http').Server(app);
var io = require('socket.io')(http);
var mysql = require('mysql');
var fs = require('fs');
// var ini_ = require('ini');
// var config = ini_.parse(fs.readFileSync('./credentials/mysql_password_db.cnf', 'utf-8'));


app.get('/', function(req, res){
  res.sendFile(__dirname + '/views/index.html');
});

//enter database info
// var con = mysql.createConnection({
//  host: config.ds410.host,
//  user: config.ds410.user,
//  password: config.ds410.password,
//  database: "stock_prices"
// });
//
// var conTweets = mysql.createConnection({
//  host: config.ds410.host,
//  user: config.ds410.user,
//  password: config.ds410.password,
//  database: "tweets_features"
// });

var poolStock  = mysql.createPool({
 host: "usdb.yikangquant.club",
 user: "cs498cca_project",
 password: "@GHhKMMP1EH4",
 database: "stock_prices"
});

var conStock = mysql.createConnection({
 host: "usdb.yikangquant.club",
 user: "cs498cca_project",
 password: "@GHhKMMP1EH4",
 database: "stock_prices"
});

var poolTweets  = mysql.createPool({
 host: "usdb.yikangquant.club",
 user: "cs498cca_project",
 password: "@GHhKMMP1EH4",
 database: "tweets_features"
});

var conTweets = mysql.createConnection({
 host: "usdb.yikangquant.club",
 user: "cs498cca_project",
 password: "@GHhKMMP1EH4",
 database: "tweets_features"
});

conStock.connect(function(err) {
  if (err) throw err;
  // console.log("Connected!");

});


conTweets.connect(function(err) {
  if (err) throw err;
  // console.log("Connected!");

});


io.on('connection', function(socket){
  console.log('a user connected');
  /*conStock.query("SELECT * FROM stock_prices.AAPL WHERE OPEN != 'null'", function (err, result, fields) {
    if (err) throw err;
    console.log(result);
  });*/

  socket.on('update', function(ticker) {
  	var sql_statement = "SELECT * FROM stock_prices." + ticker.toUpperCase() + " WHERE OPEN != 'null'";
  	conStock.query(sql_statement, function (err, result, fields) {
	    if (err) throw err;
		//console.log(result);

		var result2 = JSON.parse(JSON.stringify(result));
		// console.log(result2);
		var data = []
		for (var i = 0; i < result2.length; i++)  {
			data.push({'time': result2[i]['TIME'], 'value': result2[i]['CLOSE']});
		}
		socket.emit("priceData", {'data': data, 'ticker': ticker});

	});
  });

  socket.on('updateTweetVolume', function(ticker) {
  	conTweets.query("SELECT * FROM " + ticker.toUpperCase() + "_1H", function (err, result, fields) {
  		if (err) throw err;
		var result2 = JSON.parse(JSON.stringify(result));
  		var bear_dict = {}; //positive
		var bull_dict = {}; //negative
		var nuetral_dict = {}; //neutral
		var temp;
		var date;
		for (var i = 0; i < result2.length; i++) {
			temp = result2[i];
			date = result2[i].DATETIME;
			bear_dict[date] = temp.BEARISH_COUNT;
			bull_dict[date] = temp.BULLISH_COUNT;
			nuetral_dict[date] = temp.NEUTRAL_COUNT;
		}
		socket.emit("tweetVolumeUpdate", {'ticker': ticker, 'bear_dict': bear_dict, 'bull_dict': bull_dict, 'nuetral_dict':nuetral_dict});
  	});
  });

  socket.on('regressionUpdate', function(ticker) {
  	conTweets.query("SELECT * FROM " + ticker.toUpperCase() + "_1H_REGRESSION", function (err, result, fields) {
  		if (err) throw err;
  		var result2 = JSON.parse(JSON.stringify(result));
  		var actual = {};
  		var fitted = {};
  		var temp;
  		var time;
  		for (var i = 0; i < result2.length; i++) {
  			temp = result2[i];
  			time = temp.time;
  			actual[time] = temp.actual;
  			fitted[time] = temp.fitted;
  		}
  		socket.emit('regressionUpdate', {'ticker': ticker, 'actual': actual, 'fitted': fitted});
  	});
  });

  socket.on('error', function(e){
		console.log(e);
  });



});



http.listen(30000, '0.0.0.0', function(){
  console.log('listening on *:3000');
});
