// These DOM elements will not be redefined, so no need to reselect them each time they are used
let startCalendar = $("#id_start_time").closest(".ui.calendar");
let endCalendar = $("#id_end_time").closest(".ui.calendar");
let machine = $("#id_machine").closest(".ui.dropdown");
let calendar_container = $("#calendar-container");

// Keep internal state
let state = {
    calendar: new Calendar(),
    reservationHandler: new ReservationHandler(),
};

function setMaxReservationTime(startDate) {
    /**
     * Updates the maximum selectable date for the end calendar, and updates its value if it is no longer valid
     */
    let maxDate = getMaxDateReservation(startDate);
    endCalendar.calendar("setting", "maxDate", maxDate);
    let endDate = endCalendar.calendar("get date");
    // If the end date is set to a non-allowed value, set it to the maximum allowed date
    if (endDate !== null && (endDate > maxDate || endDate < startDate)) {
        endCalendar.calendar("set date", maxDate);
    }
}

function getFutureReservations(machine) {
    /**
     * Retrieves future reservations for the given machine from the server
     */
    let jsonUrl = langPrefix + "/reservation/json/" + machine;
    // If the form is an edit form for a given reservation, we ask the server to ignore the given reservation
    let reservationPK = $("#reservation-form").data("reservation");
    if (reservationPK) {
        jsonUrl += "/" + reservationPK + "/";
    }
    $.getJSON(jsonUrl, function (data) {
        state.reservationHandler.reservations = data.reservations;
        let startDate = startCalendar.calendar("get date");
        // If the start date is not selected, there is no need to update its date
        if (startDate === null) return;
        if (state.reservationHandler.isReserved(startDate)) {
            // If the start date is reserved for the new machine, we clear it
            startCalendar.calendar("clear");
            endCalendar.calendar("clear");
        } else {
            // Otherwise update the maximum date for the end calendar
            setMaxReservationTime(startDate);
        }
    });
}

function getMaxDateReservation(startDate) {
    /**
     * Finds the maximum allowed date for the reservation to end on given the start date
     */
    let nextReservation = state.reservationHandler.nextReservation(startDate);
    // A reservation may be no longer than a week
    let maxDate = new Date(startDate.valueOf() + 7 * 24 * 60 * 60 * 1000 - 1);

    // The reservation must end before the next reservation starts
    if (nextReservation !== null) {
        maxDate = new Date(Math.min(maxDate.valueOf(), nextReservation.startTime.valueOf()));
    }

    // Reservations from users that cannot ignore the rules, must obey the rules
    if (!state.calendar.canIgnoreRules) {
        maxDate = modifyToFirstValid(state.calendar.rules, startDate, maxDate, 1);
    }
    return maxDate;
}

let machineOnChange = function (value, removeDisabled = true) {
    /**
     * Updates the start and end datetime selectors as well as the visual calendar on selection of a new machine
     */
    // Hide the calendar if no machine is selected
    calendar_container.toggleClass("make_hidden", !value);
    // Allow for the disabled toggle to not effect the
    if (value) {
        // Set machine for calendar
        state.calendar.machine = value;
        state.calendar.update(() => {
            // Update calendar first, then check calendar values
            getFutureReservations(value);
        });
        // To make sure that disables set at template creation is not removed at the start
        if (removeDisabled) {
            startCalendar.closest(".field").toggleClass("disabled", false);
            endCalendar.closest(".field").toggleClass("disabled", false);
        }
    } else {
        // If no machine is selected, the start and end time should be cleared
        startCalendar.calendar("clear");
        startCalendar.closest(".field").toggleClass("disabled", true);
        endCalendar.calendar("clear");
        endCalendar.closest(".field").toggleClass("disabled", true);
    }
};


// Want machine
machine.dropdown({
    onChange: machineOnChange
});

// Want to clear and disable start and end date if no machine is selected
machineOnChange(machine.dropdown("get value"), false);

// Setup start calendar
startCalendar.dateTimeCalendar({
    minDate: minDate,
    maxDate: maxDate,
    endCalendar: endCalendar,
    isDisabled: function (date, mode) {
        // Clearing the date is always allowed
        if (date === undefined) return false;

        switch (mode) {
            case "minute":
                return state.reservationHandler.isReserved(date);
            case "hour":
                date = new Date(date.valueOf());
                date.setMinutes(0, 0, 0);
                // Check if the complete period is reserved
                return state.reservationHandler.isFullPeriod(date, new Date(date.valueOf() + 60 * 60 * 1000));
            case "day":
                date = new Date(date.valueOf());
                date.setHours(0, 0, 0, 0);
                // Check if the complete period is reserved
                return state.reservationHandler.isFullPeriod(date, new Date(date.valueOf() + 24 * 60 * 60 * 1000));
            default:
                return false;
        }
    },
    onChange: function (value) {
        if (value === undefined) return true;
        // Do not change to a reserved date
        let shouldChange = !state.reservationHandler.isReserved(value);
        if (shouldChange) {
            setMaxReservationTime(value);
        }
        return shouldChange;
    },
});

// Setup end calendar
endCalendar.dateTimeCalendar({
    minDate: new Date(),
    startCalendar: startCalendar,
});

// Handles duality of events and MAKE NTNU reservations
$("#id_is_event").change(function () {
    let isChecked = $(this).is(":checked");
    if (isChecked) {
        $("#id_special").closest(".ui.checkbox").checkbox("uncheck");
    } else {
        // Want to clear selected event if event is unselected. This simplifies error handling for the view
        $("#id_event").closest(".ui.dropdown").dropdown("clear")
    }
    $("#id_event").closest(".field").toggleClass("make_hidden", !isChecked);
});

$("#id_special").change(function () {
    let isChecked = $(this).is(":checked");
    if (isChecked) {
        $("#id_is_event").closest(".ui.checkbox").checkbox("uncheck");
    } else {
        // Want to clear displayed comment if MAKE NTNU reservation is unselected. This simplifies error handling for the view
        $("#id_special_text").val("");
    }
    $("#id_special_text").closest(".field").toggleClass("make_hidden", !isChecked);
});

// Error handling for the checkboxes and their respective content. The rest of the fields are checked in their widget
$("#reservation-form").submit(function () {
    let specialTextField = $("#id_special_text");
    let eventField = $("#id_event").closest(".ui.dropdown");
    specialTextField.closest(".field").toggleClass("error", specialTextField.val() === "");
    eventField.closest(".field").toggleClass("error", eventField.dropdown("get value") === "");
    if ($("#id_special").is(":checked") && specialTextField.val() === "") {
        return false;
    } else if ($("#id_is_event").is(":checked") && eventField.dropdown("get value") === "") {
        return false;
    }
});

// Error messages should be closeable
$('.message .close').on('click', function () {
    $(this).closest('.message').transition('fade');
});