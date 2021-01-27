let gmaps = null;
const GMAPS_ZOOM_AMOUNT = 18;
const STATES_SUPPORTED = {
    "Alabama": "AL",
    "Arizona": "AZ",
    "California": "CA",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Illinois": "IL",
    "Iowa": "IA",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maryland": "MD",
    "Massachussetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Missouri": "MO",
    "Nebraska": "NE",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New York": "NY",
    "North Carolina": "NC",
    "Ohio": "OH",
    "Pennsylvania": "PA",
    "South Carolina": "SC",
    "Texas": "TX",
    "Utah": "UT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wyoming": "WY"
};

/*
 * ===============================================
 * ===============================================
 *              Core Functionality   
 * ===============================================
 * ===============================================
 */

function handleDbData(dbJson) {
    // console.log(`[client] data is ${JSON.stringify(dbJson)}`);
    const countyName = dbJson['county_name'];
    const physAd = dbJson['physical_address'];
    const mailAd = dbJson['mailing_address'];
    const email = dbJson['email_address'];
    const phoneNumber = dbJson['phone_number'];
    let website = dbJson['website'];
    const officeSupervisor = dbJson['office_supervisor'] ? dbJson['office_supervisor'] : "";
    const supervisorTitle = dbJson['supervisor_title'] ? `, ${dbJson['supervisor_title']}` : "";
    let state = physAd ? physAd['state'] : (mailAd ? mailAd['state'] : "");
    let city = physAd ? `${physAd['city']}, ` : (mailAd ? `${mailAd['city']}, ` : "");
    let zip = physAd ? physAd['zip_code'] : (mailAd ? mailAd['zip_code'] : "");
    let location = physAd ? physAd['location_name'] : (mailAd ? mailAd['location_name'] : "");
    let street = (physAd && physAd['street']) ? physAd['street'] : ((mailAd && mailAd['street']) ? mailAd['street'] : "");
    let apt = (physAd && physAd['apt_unit']) ? physAd['apt_unit'] : ((mailAd && mailAd['apt_unit']) ? mailAd['apt_unit'] : "");

    setTextClass("cinfo", "Contact Info:");
    setTextClass("cadd", "Walk your vote to:");

    const countyObj = $(".county-name");
    console.log(state);
    if (state.length !== 2) {
        caps = capitalizeFirstLetter(state);
        state = lookup2digitStateCode(caps);
    } else {
        state = state.toUpperCase();
    }

    // handle title text displaying county/city/parish name
    if(countyName) {
        countyObj.text(`${countyName} County, ${state}`);
        if (state === 'LA') {
           countyObj.text(`${countyName} Parish, ${state}`);
        }
    } else if (physAd) {
        countyObj.text(`${city} Municipality, ${state}`);
    } else if (mailAd) {
        countyObj.text(`${city} Municipality, ${state}`);
    } 

    setTextClass("phone-number", phoneNumber);

    setTextClass("email", email);
    $(".email").attr('href', `mailto:${email}`);

    setTextClass("website", "Jurisdiction website");
    if (!website.includes("http")) {
        website = `http://${website}`;
    }
    $('.website').attr('href', website);

    setTextClass("super-name", officeSupervisor);
    setTextClass("super-title", supervisorTitle);

    setTextClass("location-name", location);
    setTextClass("street-number-name", street.replace("Road", "Rd"));
    setTextClass("apt-unit", apt);
    setTextClass("city", city);
    setTextClass("state", state);
    setTextClass("zipcode", zip);

    let consolidatedAddress = `${street.replace("Road", "Rd")} ${city} ${state} ${zip}`;
    if (!street) { // no street address, try google mapsing "<county> Office of Elections"
        consolidatedAddress = `${location} ${city} ${state} ${zip}`;
    }
    updateMap(consolidatedAddress);

    $('.wtv-results-wrapper').removeClass("hidden");
    $(".request-success").removeClass("hidden");
    $(".contact-info-wrapper").removeClass("hidden");
    $(".address-wrapper").removeClass("hidden");
    $(".below-results-note").removeClass("hidden");

    $("html, body").animate({ scrollTop: $('.wtv-results-wrapper').offset().top - 45 }, 500);
}

function handleDbWarning(message, county="", state="") {
    if (!message) {
        console.log("[Warning] No error message found!");
        return;
    }
    var citystate = `${county}, ${state}`;

    $(".county-name").text(citystate);

    $(".error-wrapper").text(message)

    $('.wtv-results-wrapper').removeClass("hidden");
    $(".error-wrapper").removeClass("hidden");
    $(".request-warning").removeClass("hidden");

    $("html, body").animate({ scrollTop: $('.wtv-results-wrapper').offset().top - 45 }, 500);
}

function handleDbError(message) {
    if (!message) {
        console.log("[Error] No error message found!");
        return;
    }

    $(".county-name").text("Zipcode Lookup Error");

    $(".error-wrapper").text(message);

    $(".wtv-results-wrapper").removeClass("hidden");
    $(".error-wrapper").removeClass("hidden");
    $(".request-error").removeClass("hidden");

    $("html, body").animate({ scrollTop: $('.wtv-results-wrapper').offset().top - 45 }, 500);
}

function handleZipCode(zip) {  
    $.ajax({
        url: 'https://pog-the-vote.ue.r.appspot.com/' + 'api/' + zip,
        //url: 'http://localhost:8080/' + 'api/' + zip,
        type: 'GET',
        dataType: 'json',
        success: function(data){ 
            hideLoader();
            handleDbData(data);
        },
        error: function(xhr, options, error) {
            var errorData = JSON.parse(xhr.responseText);
            var errorMsg = "";

            hideLoader();    
            if ('state' in errorData) { // zip exists, but no data yet
                handleDbWarning(errorData["message"], errorData["county"], errorData["state"]);
            } else { 
                if ('message' in errorData) { // zip is invalid/doesn't exist
                    errorMsg = errorData["message"];
                } else {
                    errorMsg = `Error: ${xhr.status}: ${xhr.statusText}.\n Response is: ${xhr.responseText}`;
                }
                handleDbError(errorMsg);
            }
            clearZipFields();
        }
    });   
}

 function initMap() {
    let mapEl = document.getElementById("map");
    const uluru = {
        lat: -25.3,
        lng: 131
    }
    gmaps = new google.maps.Map(mapEl, {
        zoom: 6,
        center: uluru
    });
    
    // const marker = new google.maps.Marker({
    //     position: uluru,
    //     map: gmaps
    // });
}

function updateMap(address) {
    geocoder = new google.maps.Geocoder();
    geocoder.geocode({address: address}, (results, status) => {
        if (status === "OK") {
            let loc = results[0].geometry.location;
            gmaps.setCenter(loc);
            var listener = google.maps.event.addListenerOnce(gmaps, "idle", function() {
                gmaps.setZoom(GMAPS_ZOOM_AMOUNT);
                new google.maps.Marker({
                    map: gmaps,
                    position: loc
                });
            })
            $("#map").removeClass("hidden");
        } else { // TODO: display error message here
            console.log(`[ERROR] Failed geocoding address ${address} for reason ${status}`);
        }
    });
    // console.log(address);
}

function populateStates() {
    for (let state in STATES_SUPPORTED) {
        let stateString = `<li>${state}</li>`;
        $(".states-supported-list").append(stateString);
    }

    console.log(`# of states supported: ${Object.keys(STATES_SUPPORTED).length}`);
}

function lookup2digitStateCode(state) {
    return STATES_SUPPORTED[state] ? STATES_SUPPORTED[state] : state;
}

/*
 * ===============================================
 * ===============================================
 *                     UI/UX
 * ===============================================
 * ===============================================
 */

/* ===============================================                    
 *        Delivers zip code to the core fn 
 *               ----------------
 *  - If you want something to happen right when the user requests
 *    their information, put it in this function*
 * ===============================================
 */

function consolidateZipInputs() {
    showLoader(); //* this is an example of an action that fires right when the AJAX request starts
                  //  just shows the fun little spinning loader :)

    somedataLayerTrackingfunction();

    $('.wtv-results-wrapper').addClass("hidden");
    $(".request-success").addClass("hidden");
    $(".request-warning").addClass("hidden");
    $(".request-error").addClass("hidden");
    $(".error-wrapper").addClass("hidden");
    $(".contact-info-wrapper").addClass("hidden");
    $(".address-wrapper").addClass("hidden");
    $(".below-results-note").addClass("hidden");
    $("#map").addClass("hidden");
    handleUnfocus();
    
    let res = "";
    $(".desktop").each(function() {
        res += $(this).val();
    });
    if (res === "") { // zip input is empty, try mobile
        res = $("#zipmobile").val();
    }
    handleZipCode(res);
}

function clearZipFields() {
    $("input").each(function() {
        $(this).val("");
        $(this).removeClass("active-input");
    });
}

function handleZipKeydown(evt) {
    let char = String.fromCharCode(evt.which);
    let numericOnly = char.replace(/[^0-9\.]/g,'');
    let valueBeforeInput = $(this).val();
    let value = $(this).val() + char;

    let thisInputId = $(this)[0].id.split('zip')[1]
    let nextInput = $(`#zip${parseInt(thisInputId) + 1}`);
    let previousInput = $(`#zip${parseInt(thisInputId) - 1}`);
    if (value.length == 1 && evt.which != 9) { //9 is the tab character
        setTimeout(function() {
            if (numericOnly !== '') {
                nextInput.focus();
            }
        }, 50);
    }

    if (evt.which == 9) {
        nextInput.focus();
    }

    if (evt.which == 8){
        //if (thisInputId !== 1) {
            //previousInput.focus();
        //}
    }

    if (evt.which == 13) { //enter key
        if (thisInputId == 5) {
            consolidateZipInputs();
        }
    }

    if (evt.which == 8) { //backspace key
        console.log("this is value: " + value);
        if (valueBeforeInput === '') {
            previousInput.focus();
        }
    }

    if (numericOnly === '' && evt.which != 37 && evt.which != 39 && evt.which != 8) {
        return false;
    }
    if (value.length > 1 && evt.which != 37 && evt.which != 39 && evt.which != 8) {
        return false;
    }
}

function handleZipFocus(e) {
    let thisInputId = $(this)[0].id.split('zip')[1]
    $(".desktop").each(function() {
        let loopZipId = $(this)[0].id.split('zip')[1];
        if (loopZipId == thisInputId) {
            $(this).addClass("active-input");
        } else {
            $(this).removeClass("active-input");
        }
    });
}

function handleUnfocus() {
    $(".desktop").each(function() {
        $(this).removeClass("active-input");
    })
}

/*
 * ===============================================
 * ===============================================
 *                  Helper Functions
 * ===============================================
 * ===============================================
 */

function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
}

function setTextClass(className, stringToSet) {
    $(`.${className}`).text(stringToSet);
}

function hideLoader() {
    $(".wtv-loader").hide();
}

function showLoader() {
    $(".wtv-loader").show();
}

/*
 * ===============================================
 * ===============================================
 *                  Document Ready
 * ===============================================
 * ===============================================
 */

$(document).ready(function() {
    if ($(window).width() >= 577) {
        $(".desktop").on('keydown', handleZipKeydown);
        $(".desktop").on('focus', handleZipFocus);
        $(".desktop").on('blur', handleUnfocus);
    }
    populateStates();
});

