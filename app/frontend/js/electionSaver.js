function consolidateZipInputs() {
    showLoader();
    let res = "";
    $("input").each(function() {
        res += $(this).val();
    });
    handleZipCode(res);
}

function hideLoader() {
    $(".loader").hide();
}

function showLoader() {
    $(".loader").show();
}

function handleDbData(dbJson) {
    console.log(`[client] data is ${JSON.stringify(dbJson)}`);

    $(".county-name").text(dbJson['county_name'] + " County");
    $('.phone-number').text(dbJson['phone_number']);

    $('.email').text(dbJson['email_address']);
    $('.email').attr('href', 'mailto:' + dbJson['email_address']);

    $('.website').text(dbJson['website']);
    $('.website').attr('href', dbJson['website']);

    if (dbJson['office_supervisor']) {
        console.log(`[client] Supervisor is ${dbJson['office_supervisor']}`);
        $('.super-name').text(dbJson['office_supervisor']);
    }

    if (dbJson['supervisor_title']) {
        $('.super-title').text(dbJson['supervisor_title']);
    }

    let physAd = dbJson['physical_address'];

    if (physAd['location_name']) {
        $('.location-name').text(physAd['location_name']);
    }

    if (physAd['street']) {
        $('.street-number-name').text(physAd['street']);
    }

    if (physAd['apt_unit']) {
        $('.apt-unit').text(physAd['apt_unit']);
    }
    
    $('.city').text(physAd['city']);
    $('.state').text(physAd['state']);
    $('.zipcode').text(physAd['zip_code']);

    $('.wtv-results-wrapper').removeClass("hidden");
}

function handleZipCode(zip) {  
    $.ajax({
        url: 'http://localhost:5000/' + zip,
        type: 'GET',
        dataType: 'json',
        success: function(data){ 
            hideLoader();

            $(".zip-text").text(zip);

            try {
                electionOfficeData = data.parent_city.parent_county.election_office;
                handleDbData(electionOfficeData);
            } catch (error) {
                console.error(error);
            }
        },
        error: function(xhr, options, error) {
            alert(`Error: ${xhr.status}: ${xhr.statusText}`); //or whatever
        }
    });   
}

$(document).ready(function() {
    $("input").on('keydown', function(evt) {
        let numericOnly = $(this).val().replace(/[^0-9\.]/g,'');
        let value = $(this).val() + String.fromCharCode(evt.which);
        if (value.length == 1 && evt.which != 9) { //9 is the tab character
            let thisInputId = $(this)[0].id.split('zip')[1]
            let nextInput = $(`#zip${parseInt(thisInputId) + 1}`);
            setTimeout(function() {
                nextInput.focus();
            }, 100);
        }
        if (value.length > 1) {
            return false;
        }
    });
})