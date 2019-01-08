class ReservationRule {
    /**
     * Class indicate a single reservation rule
     * @param periods The periods for which the rule is valid
     * @param maxInside The maximum duration of a reservation solely inside on of the periods of the rule
     * @param maxCrossed The maximum duration of a reservation inside this rule if the reservation is inside several
     *                   periods of this or other rules
     */
    constructor(periods, maxInside, maxCrossed) {
        this.periods = periods;
        this.maxInside = maxInside;
        this.maxCrossed = maxCrossed;
    }


    static dateToWeekRep(date) {
        /**
         * Converts a date to the week representation used for reservation rules [0, 7)
         */
        return (date.getDay() + 6) % 7 + date.getHours() / 24 + date.getMinutes() / 1440 + date.getSeconds() / 86400;
    }

    hoursInside(startTime, endTime) {
        /**
         * Calculates how many hours the period [startTime, endTime] overlap with this rule
         */
        startTime = ReservationRule.dateToWeekRep(startTime);
        endTime = ReservationRule.dateToWeekRep(endTime);
        let hours = 0;
        this.periods.forEach(function (period) {
            hours += overlap(period[0], period[1], startTime, endTime, 7) * 24;
        });
        return hours.toPrecision(4);
    }
}

function duration(startTime, endTime) {
    /**
     * Calculates the duration of the time period [startTime, endTime] in hours
     */
    return (endTime.valueOf() - startTime.valueOf()) / (60 * 60 * 1000);
}


function overlap(a, b, c, d, mod) {
    /**
     * Finds the overlap of period [a, b] with period [c, d] given a modulo of the periods (e.g. wrapping week)
     */
    b = (b - a + mod) % mod;
    c = (c - a + mod) % mod;
    d = (d - a + mod) % mod;
    if (c > d) {
        return Math.min(b, d);
    } else {
        return Math.min(b, d) - Math.min(b, c);
    }
}

function inside(a, b, c, mod) {
    /**
     * Checks if c is inside the period defined by [a, b]
     */
    b = (b - a + mod) % mod;
    c = (c - a + mod) % mod;
    return c <= b;
}


function getPeriodIn(rules, date, direction) {
    date = (date.getDay() + 6) % 7 + date.getHours() / 24 + date.getMinutes() / 1440;
    for (let rule of rules) {
        for (let period of rule.periods) {
            if (direction === 1 && period[0] === date || direction === 0 && period[1] === date) {
                continue;
            }
            if (inside(period[0], period[1], date, 7)) {
                return {
                    "startTime": period[0],
                    "endTime": period[1],
                    "maxInside": rule.maxInside,
                    "maxCrossed": rule.maxCrossed,
                }
            }
        }
    }
}

function getRulesCovered(rules, startTime, endTime) {
    /**
     * Returns the rules which overlap with the period [startTime, endTime]
     */
    return rules.filter(rule => rule.hoursInside(startTime, endTime) > 0);
}

function isValidForRules(rules, startTime, endTime) {
    /**
     * Checks if the period [startTime, endTime] is valid for the given set of rules
     */
    let coveredRules = getRulesCovered(rules, startTime, endTime);
    // Special handling of reservations withing a single period
    if (coveredRules.length === 1) {
        return coveredRules[0].maxInside >= coveredRules[0].hoursInside(startTime, endTime);
    }

    // If the reservation is shorter than the maximum inside value for any of the rules, it should also be valid for
    // the whole duration, even though it breaks with one or more of the max_crossed rules.
    let minTime = Math.min.apply(null, coveredRules.map(rule => rule.maxInside));
    if ((endTime.valueOf() - startTime.valueOf()) / (60 * 60 * 1000) <= minTime) {
        return true;
    }

    let maxTime = 0;
    for (let rule of coveredRules) {
        maxTime = Math.max(maxTime, rule.maxInside);
        if (rule.maxCrossed < rule.hoursInside(startTime, endTime)) {
            return false;
        }
    }
    return (endTime.valueOf() - startTime.valueOf()) / (60 * 60 * 1000) <= maxTime;
}

function modifyToFirstValid(rules, startTime, endTime, modificationDirection) {
    /**
     * Modifies either startTime (modificationDirection 0) or endTime (modificationDirection 1) until the period
     * [startTime, endTime] is valid for the given set of rules.
     */
    // Check if the period is valid for the set of rules
    while (!isValidForRules(rules, startTime, endTime)) {
        // Get all rules the start/end time overlap
        let coveredRules = getRulesCovered(rules, startTime, endTime);

        // Check if the total time of the reservation is greater than what is allowed by the covered rules
        let maxTime = Math.max.apply(null, coveredRules.map(rule => rule.maxInside));
        let minTime = Math.min.apply(null, coveredRules.map(rule => rule.maxInside));

        // Modify the start/end time based on the maximum allowed time for the covered rules
        if (maxTime < duration(startTime, endTime)) {
            if (modificationDirection) {
                endTime = new Date(startTime.valueOf() + maxTime * 60 * 60 * 1000);
            } else {
                startTime = new Date(endTime.valueOf() - maxTime * 60 * 60 * 1000);
            }
            continue;
        }

        // If the period is still not valid, this means that we have to remove the rules one by one
        let period = getPeriodIn(rules, modificationDirection ? endTime : startTime, modificationDirection);
        if (modificationDirection) {
            let currentOverlap = (overlap(period.startTime, period.endTime, period.startTime, ReservationRule.dateToWeekRep(endTime), 7) * 24);
            // Shrink the overlap until
            if (currentOverlap > period.maxInside) {
                // If the overlap with the current time period is greater than the maximum allowed inside then
                // shrink till it is equal to that.
                endTime = new Date(endTime.valueOf() - (currentOverlap - period.maxInside) * 60 * 60 * 1000);
            } else if (currentOverlap > period.maxCrossed) {
                // If the overlap with the current time period is greater than the maximum allowed when multiple
                // time periods are selected, then shrink till it is equal to that.
                endTime = new Date(Math.max(
                    endTime.valueOf() - (currentOverlap - period.maxCrossed) * 60 * 60 * 1000,
                    startTime.valueOf() + minTime * 60 * 60 * 1000
                ));
            } else {
                // If the overlap is smaller than both the allowed inside when single- and multi-period, shrink till
                // there is no overlap between the periods.
                endTime = new Date(Math.max(
                    endTime.valueOf() - currentOverlap * 60 * 60 * 1000,
                    startTime.valueOf() + minTime * 60 * 60 * 1000
                ));
            }
        } else {
            let currentOverlap = (overlap(period.startTime, period.endTime, ReservationRule.dateToWeekRep(startTime), period.endTime, 7) * 24);
            if (currentOverlap > period.maxInside) {
                // If the overlap with the current time period is greater than the maximum allowed inside then
                // shrink till it is equal to that.
                startTime = new Date(startTime.valueOf() + (currentOverlap - period.maxInside) * 60 * 60 * 1000);
            } else if (currentOverlap > period.maxCrossed) {
                // If the overlap with the current time period is greater than the maximum allowed when multiple
                // time periods are selected, then shrink till it is equal to that.
                startTime = new Date(Math.min(
                    startTime.valueOf() + (currentOverlap - period.maxCrossed) * 60 * 60 * 1000,
                    endTime.valueOf() - minTime * 60 * 60 * 1000
                ));
            } else {
                // If the overlap is smaller than both the allowed inside when single- and multi-period, shrink till
                // there is no overlap between the periods.
                startTime = new Date(Math.min(
                    startTime.valueOf() + currentOverlap * 60 * 60 * 1000,
                    endTime.valueOf() - minTime * 60 * 60 * 1000
                ));

            }
        }
    }
    return modificationDirection ? endTime : startTime;
}
