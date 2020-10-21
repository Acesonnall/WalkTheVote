/*
 * ===============================================
 * ===============================================
 *              Imports & declarations
 * ===============================================
 * ===============================================
 */

var chalk = require('chalk');

var connected = chalk.bold.cyan;
var error = chalk.bold.yellow;
var disconnected = chalk.bold.red;
var termination = chalk.bold.magenta;

const express = require('express');
const mongoose = require('mongoose');
const path = require('path');
const cors = require('cors');
const yes = require('yes-https');
const compression = require('compression');
require('dotenv').config();

const Schema = mongoose.Schema;
const tempPath = path.resolve(__dirname);
const _modelsdir = path.resolve(tempPath, 'models');
const ZipCode = require(path.resolve(_modelsdir, 'zip_code.js')).ZipCode;
const County = require(path.resolve(_modelsdir, 'county.js')).County;
const City = require(path.resolve(_modelsdir, 'city.js')).City;
const State = require(path.resolve(_modelsdir, 'state.js')).State;

const app = express();
const r = express.Router();

app.use(cors());
app.use(yes());
app.use(compression());

const PORT = process.env.PORT || 8080;

/*
 * ===============================================
 * ===============================================
 *               Mongo interactions
 * ===============================================
 * ===============================================
 */

mongoose.connect(process.env.PROD_DB_URL, {
    useNewUrlParser: true,
    useUnifiedTopology: true
});

mongoose.connection.on('connected', function () {
    console.log(connected(`[ElectionSaver] Mongoose successfully connected to database.`));
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
            if (data && data.length == 0) {
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
/*
 * ===============================================
 * ===============================================
 *                 Utility functions
 * ===============================================
 * ===============================================
 */

function validateZip(zipCode) {
    const regex = /^[0-9]{5}/g;
    const found = zipCode.match(regex);
    return ((found != null) && zipCode.length == 5);
}
   
function printAddress(address) {
    console.log(`address: ${address['location_name']}`);
    console.log(`         ${address['street']}`);
    if (address['apt_unit']) { console.log(`         ${address['apt_unit']}`); }
    console.log(`         ${address['city']}, ${address['state']} ${address['zip_code']}`);
}

function displayObject(value, key) {
    if (key !== '_cls') {
        if (key.includes('physical') || key.includes('mailing')) {
            console.log(`Found an address: ${key}`);
            printAddress(value);
        }
        else {
            console.log(`${key}: ${value}`);
        }
    } 
}

function deleteClsFromAddressObject(obj, addtype) {
    if (obj != null && obj.get(addtype)) { delete obj.get(addtype)['_cls']; }
}

function cleanClsFromAddresses(addobj) {
    deleteClsFromAddressObject(addobj, 'physical_address');
    deleteClsFromAddressObject(addobj, 'mailing_address');
}

/*
 * ===============================================
 * ===============================================
 *                  Express routing
 * ===============================================
 * ===============================================
 */

app.get('/faq', function(req, res) {
    let tob = path.join(__dirname + '/client/views/faq.html');
    res.sendFile(tob);
});

app.get('/maps', function(req, res) {
    let tob = path.join(__dirname + '/client/views/maps.html');
    res.sendFile(tob);
});

app.get('/help', function(req, res) {
    let tob = path.join(__dirname + '/client/views/help.html');
    res.sendFile(tob);
});

app.get('/', function(req, res) {
    let tob = path.join(__dirname + '/client/views/index.html');
    res.sendFile(tob);
});

app.get("/api/:zipcode", (req, res) => {
    const zipCode = req.params.zipcode;
    console.log(" ====== NEW LOOKUP ======");
    console.log(`Looking up data for zip code: ${zipCode}`);
    if (validateZip(zipCode)) {
        res.setHeader('Content-Type', 'application/json');
        lookupByZip(zipCode)
            .then((jsonData) => {
                console.log("======= RESULTS ======")
                let finalres = null;
                try {
                    finalres = jsonData.parent_city.parent_county.election_office
                    finalres.forEach(displayObject);
                    finalres.delete('_cls');
                } catch (error) {
                    console.log(`Error displaying data: ${error}. \nThis is most likely a city. Switching display code accordingly.`);
                    try {
                        let cityOff = jsonData.parent_city.election_office;
                        cityOff.forEach(displayObject);
                        finalres = cityOff;
                        finalres.delete('_cls');
                    } catch (error) {
                        console.log(`Error: ${error}`);
                        if (jsonData === undefined) {
                            return res.status(500).send({
                                "message": `No data found for input ${zipCode}.  Not a valid US zip code.`
                            });
                        }
                        else {
                            let splitGeoData = jsonData.parent_city._id.split(".");
                            return res.status(501).send({
                                "message": `We're still under construction! Your state is not yet supported. We're adding new states to the datbase every day, so check back soon!`,
                                "county": splitGeoData[1],
                                "state": splitGeoData[0]
                            });
                        }
                    }
                }

                cleanClsFromAddresses(finalres);

                return res.status(200).json(finalres);
            });
    }
});

app.listen(PORT, () => console.log(`Server started on port: http(s)://localhost:${PORT}`));

app.use(express.static('client'));
