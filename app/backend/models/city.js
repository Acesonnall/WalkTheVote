const mongoose = require('mongoose')

const {Schema} = mongoose;

const opts = {
    toObject: {virtuals: true},
    toJSON: {virtuals: true},
    collection: 'city'
}
const citySchema = new Schema({
    _id: {
        type: String,
        required: true
    },
    parent_county: {
        type: String,
        ref: 'County',
        required: true
    },
    election_office: {
        type: Map
    }
}, opts)

citySchema.virtual('city').get(function () {
    return this._id
})

module.exports.City = mongoose.model(`City`, citySchema);