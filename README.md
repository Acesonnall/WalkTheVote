# FindMySOE
An app that returns the address for the SOE office when given a zip-code.

How to connect to the test db:
- [install mongodb locally](https://docs.mongodb.com/manual/administration/install-community/)
- make sure mongodb is started as per the installation for your os
- open up a terminal
- type ```mongo```
- type ```use ptv-test```
- type ```db.auth("ptv-testAdmin", "T2020Electi0nSaver")
- if you see ```1``` returned on the next line you're in bayeee
- type ```db.senatorsWhoSuck.find()```
- you should see the correct senator returned, which demonstrates you're good to go