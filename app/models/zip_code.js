const mongoose = require('mongoose')

const {Schema} = mongoose;

const opts = {
    toObject: {virtuals: true},
    toJSON: {virtuals: true},
    collection: 'zip_code'
}
const zipCodeSchema = new Schema({
    _id: {
        type: String,
        minLength: 5,
        maxLength: 5,
        required: true
    },
    parent_city: {
        type: String,
        ref: 'City',
        required: true
    }
}, opts)

zipCodeSchema.virtual('zipCode').get(function () {
    return this._id
})

module.exports.ZipCode = mongoose.model(`ZipCode`, zipCodeSchema);