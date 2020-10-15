const mongoose = require('mongoose')

const {Schema} = mongoose;

const opts = {
    toObject: {virtuals: true},
    toJSON: {virtuals: true},
    collection: 'state'
}
const stateSchema = new Schema({
    _id: {
        type: String,
        required: true
    }
}, opts)

stateSchema.virtual('state').get(() => {
    return this._id
})

module.exports.State = mongoose.model(`State`, stateSchema);
