var app = require('express')();
var http = require('http').Server(app);
var io = require('socket.io')(http);
var mysql = require('mysql');
var fs = require('fs');
// var ini_ = require('ini');
// var config = ini_.parse(fs.readFileSync('./credentials/mysql_password_db.cnf', 'utf-8'));


app.get('/', function (req, res) {
    res.sendFile(__dirname + '/views/index.html');
});


var pool = mysql.createPool({
    host: "usdb.yikangquant.club",
    user: "cs498cca_web",
    password: "@cs498cca_web",
    database: "stock_prices"
});


io.on('connection', function (socket) {
    console.log('a user connected');

    socket.on('update', function (ticker) {
        var sql_statement = "SELECT * FROM stock_prices." + ticker.toUpperCase() + " WHERE OPEN != 'null'";
        pool.getConnection(function (err, connection) {
            // Use the connection
            connection.query(sql_statement, function (err, result) {
                if (err) {
                    console.log(err);
                }
                ;
                // And done with the connection.
                var result2 = JSON.parse(JSON.stringify(result));
                // console.log(result2);
                var data = []
                for (var i = 0; i < result2.length; i++) {
                    data.push({'time': result2[i]['TIME'], 'value': result2[i]['CLOSE']});
                }
                socket.emit("priceData", {'data': data, 'ticker': ticker});
                connection.release();
                // Don't use the connection here, it has been returned to the pool.
            });
        });

    });

    socket.on('updateTweetVolume', function (ticker) {
        var sql_statement = "SELECT * FROM " + ticker.toUpperCase() + "_1H";
        pool.getConnection(function (err, connection) {
            // Use the connection
            connection.query(sql_statement, function (err, result) {
                if (err) {
                    console.log(err);
                }
                // And done with the connection.
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
                socket.emit("tweetVolumeUpdate", {
                    'ticker': ticker,
                    'bear_dict': bear_dict,
                    'bull_dict': bull_dict,
                    'nuetral_dict': nuetral_dict
                });
                // Don't use the connection here, it has been returned to the pool.
            });
        });

    });

    socket.on('regressionUpdate', function (ticker) {
        sql_statement = "SELECT * FROM " + ticker.toUpperCase() + "_1H_REGRESSION";
        pool.getConnection(function (err, connection) {
            // Use the connection
            connection.query(sql_statement, function (err, result) {
                if (err) {
                    console.log(err);
                }
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
    });

    socket.on('error', function (e) {
        console.log(e);
    });


})
;


http.listen(30000, '0.0.0.0', function () {
    console.log('listening on *:3000');
});
