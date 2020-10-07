var chalk = require('chalk');

var connected = chalk.bold.cyan;
var error = chalk.bold.yellow;
var disconnected = chalk.bold.red;
var termination = chalk.bold.magenta;

const express = require('express');
const mongoose = require('mongoose');
const Schema = mongoose.Schema;

const ZipCodeSchema = new Schema({
    _id: {
        type: String,
        required: true
    },
    _cls: {
        type: String,
        required: true
    },
    parent_city: {
        type: String,
        required: true
    }
}, {
    collection: 'zip_code'
});

const app = express();
const PORT = 5000;

mongoose.connect('mongodb://ptv-testAdmin:T2020Electi0nSaver@35.231.244.29:27017/ptv-test?authSource=ptv-test', {
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

function lookupByZip(zipCode) {
    var Zip = mongoose.model('zip_code', ZipCodeSchema);
    Zip.find({_id: {$eq: zipCode}}, function(err, data) {
        result = data;
        console.log(`data is: ${data}`);
        if (err) {
            console.log(`[ERROR] Error finding value ${zipCode} in database: ${err}`);
            result = {"error": err};
        }
        return result;
    });
}

function validateZip(zipCode) {
    const regex = /^[0-9]{5}/g;
    const found = zipCode.match(regex);
    return ((found != null) && zipCode.length == 5);
}

app.get("/:zipcode", (req, res) => {
    console.log(`Request parameter is ${req.params.zipcode}`);
    if (validateZip) {
        res.json(lookupByZip(req.params.zipcode));
    }
});

app.listen(PORT, () => console.log(`Server started on port: http://localhost:${PORT}`));

//lookupByZip("33028");




