
function getMaxDateReservation(date) {
    /**
     *  Finds the latest date at which a reservation which starts at the given date can end and still be valid.
     */
    let maxDate = new Date(date.valueOf());
    let shouldRestrictToRules = !canIgnoreRules;
    if ($("#event_checkbox input").is(':checked') || $("#special_checkbox input").is(":checked")) {
        maxDate.setDate(maxDate.getDate() + 56);
        shouldRestrictToRules = false;
    } else {
        // Normal reservations should never be more than 1 week
        maxDate = new Date(maxDate.valueOf() + 7 * 24 * 60 * 60 * 1000 - 1000)
    }
    for (let index = 0; index < reservations.length; index++) {
        if (date <= reservations[index].start_time && reservations[index].start_time < maxDate)
            maxDate = new Date(reservations[index].start_time.valueOf());
    }
    if (shouldRestrictToRules) {
        // If the user/reservation type cannot ignore rules, shrink the reservation until it
        // is valid given the rules for the machine type
        return modifyToFirstValid(reservationRules, date, maxDate, 1);
    }
    return maxDate
}

function updateMaxEndDate() {
    /**
     * Updates the max date of the calender indicating the end time of the reservation.
     */
    let currentStartDate = $("#start_time").calendar("get date");
    if (currentStartDate !== null) {
        $("#end_time").calendar("setting", 'maxDate', getMaxDateReservation(currentStartDate));
    }
}

$('.ui.dropdown').dropdown();
$('#event_checkbox').checkbox({
    onChange: function () {
        $("#event_name_input").toggleClass("make_hidden", !$(this).is(':checked'));
        if ($(this).is(':checked')) {
            $('#special_checkbox').checkbox("uncheck");
            $("#start_time").calendar("setting", "maxDate", null);
        } else {
            $("#start_time").calendar("setting", "maxDate", maximum_day);
        }
        updateMaxEndDate();
    },
});
$('#special_checkbox').checkbox({
    onChange: function () {
        $("#special_input").toggleClass("make_hidden", !$(this).is(':checked'));
        if ($(this).is(':checked')) {
            $('#event_checkbox').checkbox("uncheck");
            $("#start_time").calendar("setting", "maxDate", null);
        } else {
            $("#start_time").calendar("setting", "maxDate", maximum_day);
        }
        updateMaxEndDate();
    },
});

$('#machine_name_dropdown').dropdown("set selected", $('.selected_machine_name').data("value")).dropdown('setting', "onChange", function (value) {
    if (value !== "default" && value !== "") {
        getFutureReservations(value, true);
        updateReservationCalendar();
    }
    $("#start_time > div, #end_time > div").toggleClass('disabled', value === "default");
    $("#start_time, #end_time").calendar('clear');
});


$('form').submit(function (event) {
    let is_valid = true;
    $("#machine_name_dropdown").toggleClass("error_border", false);
    $("#start_time").find("input").toggleClass("error_border", false);
    $("#end_time").find("input").toggleClass("error_border", false);
    $("#event_pk").toggleClass("error_border", false);


    if ($("#machine_name_dropdown").dropdown("get value") === "default") {
        $("#machine_name_dropdown").toggleClass("error_border", true);
        is_valid = false;
    }

    if ($("#start_time").calendar("get date") === null) {
        $("#start_time").find("input").toggleClass("error_border", true);
        is_valid = false;
    }

    if ($("#end_time").calendar("get date") === null) {
        $("#end_time").find("input").toggleClass("error_border", true);
        is_valid = false;
    }

    if ($("#event_checkbox input").is(':checked') && $("#event_pk").dropdown("get value") === "") {
        $("#event_pk").toggleClass("error_border", true);
        is_valid = false;
    }

    if (!is_valid) return event.preventDefault();
});

$('.message .close').on('click', function () {
    $(this).closest('.message').transition('fade');
});
updateReservationCalendar();

