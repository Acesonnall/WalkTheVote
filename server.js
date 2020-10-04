`use strict`;

const express = require(`express`),
    app = express(),
    readline = require(`readline`),
    find = require(`find-process`),
    http = require(`http`),
    HTTP_PORT = 80,
    path = require('path')

global.appRoot = path.resolve(__dirname);

// Require our database configurations
const mongoose = require('mongoose'),
    dbConfig = require(path.resolve(__dirname, 'config', 'database.js')),
    _modelsdir = path.resolve(appRoot, 'app', 'models'),
    ZipCode = require(path.resolve(_modelsdir, 'zip_code.js')).ZipCode,
    County = require(path.resolve(_modelsdir, 'county.js')).County,
    City = require(path.resolve(_modelsdir, 'city.js')).City,
    State = require(path.resolve(_modelsdir, 'state.js')).State

// TODO: Get signed certificate with Let's Encrypt to enable HTTPS on our website
// let options = {
//     key: process.env.LETSENCRYPT_PRIVATEKEY.replace(/\\n/g, '\n'), // replace because env vars need to be specially formatted
//     cert: process.env.LETSENCRYPT_FULLCHAIN.replace(/\\n/g, '\n') // replace because env vars need to be specially formatted. Important to use Full-Chain
// };

const server = {
    // https: https.createServer(options, app),
    http: http.createServer(app)
};

mongoose.connect(dbConfig.uri,
    {
        useNewUrlParser: true,
        useUnifiedTopology: true
    }
).then((res) => {
    console.log(`Connection to '${dbConfig.name}' Database: Established.`);

    server.http.on(`error`, onErrorHTTP);
    server.http.on(`listening`, onListeningHTTP);
    server.http.listen(HTTP_PORT);

    // Without populate, parent_city would just be a sting
    ZipCode.findById("75801").populate({
        path: 'parent_city',
        populate: {
            path: 'parent_county',
            populate: {
                path: 'parent_state'
            }
        },
    }).exec((err, doc) => {
        console.log(doc.parent_city)
    })
}).catch(err => {
    let asterisks = ``,
        i;
    for (i = 0; i < err.toString().length; i++) {
        asterisks += `*`
    }
    console.log(`Connection to '${dbConfig.name}' Database: Failed.
    ${asterisks}
    ${err}
    ${asterisks}`);
});

function EADDRINUSE_Helper(server, port) {
    find(`port`, port)
        .then(list => {
            if (!list.length)
                console.log(`port %d is now free.`, port);
            else {
                const rl = readline.createInterface({
                    input: process.stdin,
                    output: process.stdout,
                    prompt: `Found ${list[0].name} (PID ${list[0].pid}) listening on port ${port}, initiated by PID ${list[0].ppid}. Would you like to kill it? (Y/N)> `
                });

                rl.prompt();

                rl.on(`line`, line => {
                    switch (line.trim().toLowerCase()) {
                        case `yes`:
                        case `y`:
                            try {
                                process.kill(list[0].pid);
                            } catch (e) {
                                console.error(`PID ${list[0].pid} does not exit or exists under another PID. Error code: ${e.code}`)
                            }
                            console.log(`Retrying...`);
                            setTimeout((server, port) => {
                                server.close();
                                server.listen(port);
                            }, 1000, server, port);
                            break;
                        case `no`:
                        case `n`:
                            console.log(`Exiting application.`);
                            process.exit(1);
                            break;
                        default:
                            rl.prompt();
                    }
                });
            }
        });
}

function onErrorHTTP(err) {
    if (err.syscall !== `listen`) throw err;

    const bind = `${typeof HTTP_PORT === 'string'
        ? 'Pipe ' + HTTP_PORT
        : 'Port ' + HTTP_PORT}`;

    // handle specific listen errors with friendly messages
    switch (err.code) {
        case `EACCES`:
            console.error(`${bind} requires elevated privileges`);
            process.exit(1);
            break;
        case `EADDRINUSE`:
            console.error(`${bind} is already in use, finding process...`);
            EADDRINUSE_Helper(server.http, HTTP_PORT);
            break;
        default:
            throw err;
    }
}

function onListeningHTTP() {
    const addr = server.http.address();
    const bind = `${typeof addr === 'string'
        ? 'pipe ' + addr
        : 'port ' + addr.port}`;
    console.log(`Listening on ${bind}`);
}