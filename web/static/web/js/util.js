/**
 * Returns the day of the week following the ISO-8601 format (monday is the first day of the week)
 * @returns {number} The day of the week monday = 0, sunday = 6
 */
Date.prototype.getISO8601Day = function () {
    return (this.getDay() + 6) % 7;
};

/**
 * Returns the current time of the day as hours in the range [0, 24)
 * @returns {float} The current time of day
 */
Date.prototype.toTime = function () {
    return this.getHours() + this.getMinutes() / 60 + this.getSeconds() / 3600;
};

/**
 *
 * @param hours
 */
Date.prototype.setTimeOfDay = function (hours) {
    this.setHours(hours);
    this.setMinutes(hours % 1 * 60);
};

/**
 * Return the week number of the date in the ISO-8601 format
 * @returns {int} The week number
 */
Date.prototype.getWeek = function () {
    // Copy date to not change our current date
    let copy = new Date(this.valueOf());
    // ISO-8601 defines weeks based on Thursdays
    copy.setDate(copy.getDate() - copy.getISO8601Day() + 3);
    let firstThursday = copy.valueOf();

    // Find the first thursday of the year, as that defines the first week
    copy.setMonth(0, 1);
    // If the first day of the year is not a Thursday, fast-forward to the first Thursday
    if (copy.getISO8601Day() !== 3) {
        copy.setMonth(0, 1 + (3 - copy.getISO8601Day() + 7) % 7);
    }

    // The first Thursday is in week 1, so the difference to the first Thursday is the number of weeks elapsed in the year
    return 1 + Math.ceil((firstThursday - copy) / (24 * 7 * 60 * 60 * 1000));
};

/**
 * Returns the next day
 * @returns {Date} The next day
 */
Date.prototype.nextDay = function () {
    return new Date(this.valueOf() + 24 * 60 * 60 * 1000);
};

/**
 * Returns the same time in the previous (-1/"back") or next (1/"forward") week
 * @param direction Indicates if we should cycle forwards or backwards
 * @returns {Date} The previous or next week
 */
Date.prototype.cycleWeek = function (direction) {
    switch (direction) {
        case "back":
        case -1:
            return new Date(this.valueOf() - 7 * 24 * 60 * 60 * 1000);
        case "forward":
        case 1:
            return new Date(this.valueOf() + 7 * 24 * 60 * 60 * 1000);
    }
};

/**
 * Returns the first day of the current week
 * @returns {Date} The first day of the current week (at midnight)
 */
Date.prototype.firstDayOfWeek = function () {
    return new Date(this.getFullYear(), this.getMonth(), this.getDate() - this.getISO8601Day());
};

/**
 * Capitalizes the first letter in the string
 * @returns {string} The string with the first letter in uppercase
 */
String.prototype.capitalize = function () {
    return this.charAt(0).toUpperCase() + this.slice(1)
};