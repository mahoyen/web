class Reservation {

    constructor(startTime, endTime, popup, type) {
        this.startTime = startTime;
        this.endTime = endTime;
        this.popup = popup;
        this.type = type;
    }

    /**
     * Builds the popup content for the reservation
     * @returns String representing the HTML for the popup
     */
    getPopup() {
        let wrapper = $("<div>");
        if (this.popup.header) {
            wrapper.append($("<div class='header'>" + this.popup.header + "</div>"));
        }
        for (let field of this.popup.fields) {
            let fieldElement = $("<div>");
            fieldElement.append("<b>" + field[0] + ": </b>");
            fieldElement.append("<span>" + field[1] + "</span>");
            wrapper.append(fieldElement);
        }
        return wrapper.prop("innerHTML");
    }

    /**
     * Checks if the reservation should have a popup
     * @returns {boolean}
     */
    hasPopup() {
        return this.popup.fields;
    }

    /**
     * Creates and adds reservation objects to each day of the given week that the reservation covers
     * @param weekStart The first day of the week (monday midnight)
     * @param weekEnd The end of the week (monday midnight)
     */
    setupElements(weekStart, weekEnd) {
        // Cut the reservation to the start and end of the week
        let startDay = new Date(Math.max(weekStart, this.startTime));
        let endDay = new Date(Math.min(weekEnd, this.endTime));
        let days = $("#calendar").find(".day");

        // TODO: Fix issue with Sunday to Monday in Sunday week
        for (let day = startDay.getISO8601Day(); day <= endDay.getISO8601Day(); day++) {
            // The first day of the reservation starts late
            let startTime = 0;
            if (startDay.getISO8601Day() === day) {
                startTime = startDay.toTime();
            }

            // The last day of the reservation ends early
            let endTime = 24;
            if (endDay.getISO8601Day() === day) {
                endTime = endDay.toTime();
            }
            $(days[day]).append(this.getElement(startTime, endTime))
        }
    }

    /**
     * Creates an element for the reservation for the given start time and end time
     * @param startTime The start time
     * @param endTime The end time
     * @returns {jQuery.HTMLElement} The reservation div
     */
    getElement(startTime, endTime) {
        let element = $("<div class='reservation'>");

        element.css("top", startTime / 24 * 100 + "%");
        element.css("height", (endTime - startTime) / 24 * 100 + "%");

        element.toggleClass(this.typeClass, true);

        if (this.hasPopup()) {
            element.attr("data-html", this.getPopup())
        }

        return element;
    }

    /**
     * Returns the correct css class(es) for the type of the event
     * @returns {string} The css class(es) for the event type
     */
    get typeClass() {
        switch (this.type) {
            case "event":
                return "event";
            case "make":
                return "make";
            case "user":
                return "self user";
            case "normal":
                return "user";
        }
    }
}

class ReservationHandler {

    constructor() {
        this.clear();
    }

    clear() {
        this._reservations = [];
    }

    set reservations(reservations) {
        this.clear();
        for (let reservation of reservations) {
            this._reservations.push(new Reservation(new Date(reservation.start_time), new Date(reservation.end_time), reservation.popup, reservation.type))
        }
    }

    get reservations() {
        return this._reservations.slice()
    }

    isReserved(date) {
        for (let reservation of this._reservations) {
            if (reservation.startTime < date && reservation.endTime > date) {
                return true;
            }
        }
        return false;
    }

    nextReservation(date) {
        let nextReservation = null;
        for (let reservation of this._reservations) {
            if (reservation.endTime <= date) continue;
            if (nextReservation === null || nextReservation.startTime > reservation.startTime) {
                nextReservation = reservation;
            }
        }
        return nextReservation;
    }

    reservationsInPeriod(startDate, endDate) {
        let reservations = [];
        for (let reservation of this._reservations) {
            if (reservation.startTime < endDate && reservation.endTime > startDate) {
                reservations.push(reservation);
            }
        }
        return reservations;
    }

    isFullPeriod(startDate, endDate) {
        let reservations = this.reservationsInPeriod(startDate, endDate);
        reservations.sort((a, b) => a.startTime - b.startTime);
        let date = startDate;
        for (let reservation of reservations) {
            if (reservation.startTime <= new Date(date.valueOf() + 5 * 60 * 1000)) {
                date = reservation.endTime;
            }
        }
        return endDate - date <= 5 * 60 * 1000;
    }

}

class Calendar {

    constructor(machine, displayDate = new Date()) {
        this.machine = machine;
        this.date = displayDate;
        this.rule
        this.reservationHandler = new ReservationHandler();

        // Setup actions
        let calendar = this;
        $("#next_week_button").click(function () {
            calendar.date = calendar.date.cycleWeek(1);
            calendar.update()
        });

        $("#prev_week_button").click(function () {
            calendar.date = calendar.date.cycleWeek(-1);
            calendar.update();
        });

        $("#now_button").click(function () {
            calendar.date = new Date().firstDayOfWeek();
            calendar.update();
        });

        // Do not update calendar if machine or date has not been set
        if (this.machine !== undefined && this.date !== undefined) {
            this.update();
        }
        new CalendarSelector(this);

        // Update the time indicator every minute
        setInterval(this.updateCurrentTime.bind(this), 60 * 1000)
    }

    get rules() {
        return this.ruleset;
    }

    set rules(rules) {
        this.ruleset = [];
        for (let rule of rules) {
            this.ruleset.push(new ReservationRule(rule.periods, rule.max_inside, rule.max_crossed))
        }
    }

    get canIgnoreRules() {
        if (this.ignoreRules === undefined) return false;
        return this.ignoreRules;
    }

    update(callback) {
        let calendar = this;
        $.ajax({
            url: "/reservation/api/reservations/",
            data: {
                year: this.date.getFullYear(),
                week: this.date.getWeek(),
                machine: this.machine,
            },
            cache: false,
            type: "GET",
            success: function (response) {
                $("#calendar").find(".reservation").remove();

                calendar.rules = response.rules;
                calendar.ignoreRules = response.canIgnoreRules;

                calendar.updateHeaders();
                calendar.updateCurrentTime();
                let weekStart = calendar.date.firstDayOfWeek();
                let weekEnd = weekStart.cycleWeek(1);

                calendar.reservationHandler.reservations = response.reservations;
                for (let reservation of calendar.reservationHandler.reservations) {
                    reservation.setupElements(weekStart, weekEnd)
                }

                $(".reservation").popup();
                if (callback !== undefined) {
                    callback();
                }
            },
            error: function (xhr) {
                // TODO: Error handling and displaying to user
                console.error(xhr)
            }
        });
    }

    /**
     * Updates the position and existence of the indicator line for the current time
     */
    updateCurrentTime() {
        $(".indicator.current").remove();

        // Only set the indicator line if we are viewing the current week
        if (this.date <= new Date() && new Date() < this.date.cycleWeek(1)) {
            let time_indicator = $("<div class='indicator current'>");
            time_indicator.css("top", (new Date().toTime() / 24) * 100 + "%");
            $($("#calendar").find(".day")[new Date().getISO8601Day()]).append(time_indicator);
        }
    }

    updateHeaders() {
        let headers = $("#calendar th");
        let currentDay = this.date.firstDayOfWeek();

        let compactMonthHeader = $(headers[0]).find("div");
        $(compactMonthHeader[0]).text(currentDay.toLocaleDateString(langCode, {month: "short"}).capitalize());
        $(compactMonthHeader[1]).text(currentDay.getWeek());

        let fullMonthHeader = $(headers[1]).find("div");
        $(fullMonthHeader[0]).text(currentDay.toLocaleDateString(langCode, {month: "long"}).capitalize());
        $(fullMonthHeader[1]).find("span").text(currentDay.getWeek());

        for (let dayIndex = 0; dayIndex < 7; dayIndex++) {
            let currentHeader = headers[dayIndex + 2];
            $(currentHeader).find(".title.medium").text(currentDay.getDate());
            currentDay = currentDay.nextDay();
        }
    }

    getDateDayOfWeek(dayNumber) {
        let date = new Date(this.date);
        date.setDate(date.getDate() + dayNumber);
        return date;
    }

    set machine(pk) {
        this._machine = pk
    }

    get machine() {
        return this._machine
    }

    set date(date) {
        if (date !== undefined) {
            this._date = date.firstDayOfWeek()
        }
    }

    get date() {
        return this._date
    }

}


class CalendarSelector {

    constructor(calendar) {
        this.calendar = calendar;
        this.selecting = false;

        $("#calendar").find(".day").on({
            "touchstart": this.handleMouseDown.bind(this),
            "touchend": this.handleMouseUp.bind(this),
            "touchmove": this.handleMouseMove.bind(this),
            "mousedown": this.handleMouseDown.bind(this),
            "mouseup": this.handleMouseUp.bind(this),
            "mousemove": this.handleMouseMove.bind(this),
        })
    }

    handleMouseDown(event) {
        if (this.date1 !== undefined) {
            this.date1 = undefined;
            this.date2 = undefined;
            this.selecting = false;
            this.draw()
        } else {
            this.selecting = true;
            this.date1 = this.targetToTime(event);
            this.date2 = this.targetToTime(event);
        }
    }

    handleMouseUp() {
        this.selecting = false;
    }

    handleMouseMove() {
        if (this.selecting) {
            this.date2 = this.targetToTime(event);
            this.date2 = modifyToFirstValid(this.calendar.rules, this.startTime, this.endTime, this.startTime.getTime() === this.date1.getTime());
            this.draw();
        }
    }

    get startTime() {
        return new Date(Math.min(this.date1, this.date2));
    }

    get endTime() {
        return new Date(Math.max(this.date1, this.date2));
    }

    draw() {
        let days = $("#calendar").find(".day");
        days.find(".time_selection").remove();

        let startDate = this.startTime;
        let endDate = this.endTime;

        for (let dayIndex = startDate.getISO8601Day(); dayIndex <= endDate.getISO8601Day(); dayIndex++) {
            let element = $("<div class='time_selection'>");

            let dayStartTime = 0;
            if (dayIndex === startDate.getISO8601Day()) {
                dayStartTime = startDate.toTime();
            }

            let dayEndTime = 24;
            if (dayIndex === endDate.getISO8601Day()) {
                dayEndTime = endDate.toTime();
            }

            element.css("top", dayStartTime / 24 * 100 + "%");
            element.css("height", (dayEndTime - dayStartTime) / 24 * 100 + "%");

            $(days[dayIndex]).append(element);
        }
    }

    targetToTime(event) {
        let dayObj = $(event.target).closest(".day");
        let position;
        if (event.touches !== undefined) {
            position = event.touches[0].pageY - dayObj.offset().top;
        } else {
            position = event.pageY - dayObj.offset().top;
        }

        // TODO? Move to calendar
        let date = this.calendar.getDateDayOfWeek($("#calendar").find(".day").index(dayObj));
        date.setTimeOfDay(position / dayObj.height() * 24);

        return new Date(Math.max(date, new Date()));
    }
}

// TODO? Fix queries to #calendar to the calendar object instead?
// TODO Fix selectable area
// TODO Fix allow selection
// TODO Fix CSS (simplify, fix legend)
// TODO Strong typing
