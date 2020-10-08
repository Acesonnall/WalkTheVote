var chalk = require('chalk');

var connected = chalk.bold.cyan;
var error = chalk.bold.yellow;
var disconnected = chalk.bold.red;
var termination = chalk.bold.magenta;

const express = require('express');
const mongoose = require('mongoose');
const path = require('path');
const cors = require('cors')
const Schema = mongoose.Schema;

const tempPath = path.resolve(__dirname);
const _modelsdir = path.resolve(tempPath, 'models');
const ZipCode = require(path.resolve(_modelsdir, 'zip_code.js')).ZipCode;
const County = require(path.resolve(_modelsdir, 'county.js')).County;
const City = require(path.resolve(_modelsdir, 'city.js')).City;
const State = require(path.resolve(_modelsdir, 'state.js')).State;

const app = express();
app.use(cors());
const PORT = 5000;

mongoose.connect('mongodb://ptv-testAdmin:T2020Electi0nSaver@walkthevote.us:27017/ptv-test?authSource=ptv-test', {
    useNewUrlParser: true,
    useUnifiedTopology: true
});

mongoose.connection.on('connected', function () {
    console.log(connected(`[ElectionSaver] Mongoose successfully connected to test database.`));
});

mongoose.connection.on('error', function(err){
    console.log(error(`[ElectionSaver] Error connecting to database: ${err}`));
});

mongoose.connection.on('disconnected', function(){
    console.log(disconnected("[ElectionSaver] Connection to database has been disconnected!"));
});

async function lookupByZip(zipCode) {
    const test = await ZipCode.find({_id: {$eq: zipCode}}, function(err, data) {
        if (err || data.length == 0) {
            if (data &&     data.length == 0) {
                console.log(`[ERROR] No data found!`);
            }
            console.log(`[ERROR] Error finding value ${zipCode} in database: ${err}`);
        }
    }).populate({
        path: 'parent_city',
        populate: {
            path: 'parent_county'
        }
    });
    return test[0];
}

function validateZip(zipCode) {
    const regex = /^[0-9]{5}/g;
    const found = zipCode.match(regex);
    return ((found != null) && zipCode.length == 5);
}
        
app.get("/:zipcode", (req, res) => {
    console.log(`Request parameter is ${req.params.zipcode}`);
    if (validateZip) {
        res.setHeader('Content-Type', 'application/json');
        lookupByZip(req.params.zipcode)
            .then((jsonData) => {
                console.log(`Returning data ${jsonData}`);
                return res.status(200).json(jsonData);
            });
    }
});

app.listen(PORT, () => console.log(`Server started on port: http://localhost:${PORT}`));

//lookupByZip("33028");




