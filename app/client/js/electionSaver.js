/*
 * ===============================================
 * ===============================================
 *              Core Functionality   
 * ===============================================
 * ===============================================
 */

function handleDbData(dbJson) {
    console.log(`[client] data is ${JSON.stringify(dbJson)}`);

    $(".cinfo").text("Contact Info:");
    $(".cadd").text("Walk your vote to:");

    if(dbJson['county_name']) {
        $(".county-name").text(dbJson['county_name'] + " County");
    } else if (dbJson['physical_address']) {
        $(".county-name").text(dbJson['physical_address']['city'] + " Municipality");
    } else if (dbJson['mailing_address']) {
        $(".county-name").text(dbJson['mailing_address']['city'] + " Municipality");
    }

    $('.phone-number').text(dbJson['phone_number']);

    $('.email').text(dbJson['email_address']);
    $('.email').attr('href', 'mailto:' + dbJson['email_address']);

    $('.website').text("Jurisdiction website");
    $('.website').attr('href', dbJson['website']);

    if (dbJson['office_supervisor']) {
        console.log(`[client] Supervisor is ${dbJson['office_supervisor']}`);
        $('.super-name').text(dbJson['office_supervisor'] + ",");
    }

    if (dbJson['supervisor_title']) {
        $('.super-title').text(dbJson['supervisor_title']);
    }

    if (dbJson['physical_address']) {
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
        
        $('.city').text(physAd['city'] + ",");
        $('.state').text(physAd['state']);
        $('.zipcode').text(physAd['zip_code']);
    } else {
        if (dbJson['mailing_address']) {
            let mailAd = dbJson['mailing_address'];

            if (mailAd['location_name']) {
                $('.location-name').text(mailAd['location_name']);
            }
        
            if (mailAd['street']) {
                $('.street-number-name').text(mailAd['street']);
            }
        
            if (mailAd['apt_unit']) {
                $('.apt-unit').text(mailAd['apt_unit']);
            }
            
            $('.city').text(mailAd['city'] + ",");
            $('.state').text(mailAd['state']);
            $('.zipcode').text(mailAd['zip_code']);
        }
    }

    $('.wtv-results-wrapper').removeClass("hidden");
    $(".request-success").removeClass("hidden");
    $(".contact-info-wrapper").removeClass("hidden");
    $(".address-wrapper").removeClass("hidden");
    $(".below-results-note").removeClass("hidden");

    $("html, body").animate({ scrollTop: $('.wtv-results-wrapper').offset().top - 100 }, 500);
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
}

function handleZipCode(zip) {  
    $.ajax({
        url: 'https://pog-the-vote.ue.r.appspot.com/' + 'api/' + zip,
        //url: 'http://localhost:8080/' + 'api/' + zip,
        type: 'GET',
        dataType: 'json',
        success: function(data){ 
            hideLoader();

            $(".zip-text").text(zip);

            try {
                handleDbData(data); 
            } catch (error) {
                console.error(error);
            }
        },
        error: function(xhr, options, error) { // state is not in the database
            var errorData = JSON.parse(xhr.responseText);
            var errorMsg = "";

            hideLoader();    
            if ('state' in errorData) {
                handleDbWarning(errorData["message"], errorData["county"], errorData["state"]);
            }        
            else { 
                if ('message' in errorData) {
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

    $('.wtv-results-wrapper').addClass("hidden");
    $(".request-success").addClass("hidden");
    $(".request-warning").addClass("hidden");
    $(".request-error").addClass("hidden");
    $(".error-wrapper").addClass("hidden");
    $(".contact-info-wrapper").addClass("hidden");
    $(".address-wrapper").addClass("hidden");
    $(".below-results-note").addClass("hidden");
    
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
    });
}

function handleZipKeydown(evt) {
    let char = String.fromCharCode(evt.which);
    let numericOnly = char.replace(/[^0-9\.]/g,'');
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

    if (numericOnly === '' && evt.which != 37 && evt.which != 39 && evt.which != 8) {
        return false;
    }
    if (value.length > 1 && evt.which != 37 && evt.which != 39 && evt.which != 8) {
        return false;
    }
}

/*
 * ===============================================
 * ===============================================
 *                  Helper Functions
 * ===============================================
 * ===============================================
 */

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
    }
});

