const mongoose = require('mongoose')

const {Schema} = mongoose;

const opts = {
    toObject: {virtuals: true},
    toJSON: {virtuals: true},
    collection: 'county'
}
const countySchema = new Schema({
    _id: {
        type: String,
        required: true
    },
    parent_state: {
        type: String,
        ref: 'State',
        required: true
    },
    election_office: {
        type: Map
    }
}, opts)

countySchema.virtual('county').get(() => {
    return this._id
})

module.exports.County = mongoose.model(`County`, countySchema);