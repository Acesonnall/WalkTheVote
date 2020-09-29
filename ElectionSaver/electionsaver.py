
def decodeEmail(e):
    de = ""
    k = int(e[:2], 16)

    for i in range(2, len(e)-1, 2):
        de += chr(int(e[i:i+2], 16)^k)

    return de
    
addressSchemaMapping = {
    'BuildingName': 'locationName',
    'CornerOf': 'locationName',
    'IntersectionSeparator':'locationName',
    'LandmarkName': 'locationName',
    'NotAddress': 'locationName',
    'SubaddressType': 'aptNumber',
    'SubaddressIdentifier': 'aptNumber',
    'AddressNumber': 'streetNumberName',
    'AddressNumberSuffix': 'streetNumberName',
    'StreetName': 'streetNumberName',
    'StreetNamePreDirectional': 'streetNumberName',
    'StreetNamePreModifier': 'streetNumberName',
    'StreetNamePreType': 'streetNumberName',
    'StreetNamePostDirectional': 'streetNumberName',
    'StreetNamePostModifier': 'streetNumberName',
    'StreetNamePostType': 'streetNumberName',
    'OccupancyType': 'aptNumber',
    'OccupancyIdentifier': 'aptNumber',
    'Recipient': 'locationName',
    'PlaceName': 'city',
    'USPSBoxGroupID': 'poBox',
    'USPSBoxGroupType': 'poBox',
    'USPSBoxID': 'poBox',
    'USPSBoxType': 'poBox',
    'StateName': 'state',
    'ZipCode': 'zipCode'
}