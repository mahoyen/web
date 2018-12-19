Date.prototype.djangoFormat = function (mode) {
    let zeroPad = (val) => val < 10 ? "0" + val.toString() : val.toString();
    let date = `${this.getFullYear()}-${zeroPad(this.getMonth() + 1)}-${zeroPad(this.getDate())}`;
    let time = `${zeroPad(this.getHours())}:${zeroPad(this.getMinutes())}`;

    switch (mode) {
        case "date":
            return date;
        case "time":
            return time;
        case "datetime":
            return `${date} ${time}`;
    }
};

$.fn.extend({
    dateTimeCalendar: function (attributes) {
        let defaults = {
            mode: "minute",
            firstDayOfWeek: 1,
            monthFirst: false,
            ampm: false,
            parser: {
                date: function (text, settings) {
                    return new Date(text);
                }
            },
            selector: {
                input: "input[type=text]"
            }
        };

        Object.assign(defaults, attributes);
        this.calendar(defaults);

        this.closest("form").submit(function () {
            try {
                this.find("input[type=hidden]").prop("value", this.calendar("get date").djangoFormat("datetime"));
                this.closest(".field").toggleClass("error", false);
            } catch (error) {
                if (!(error instanceof TypeError)) throw error;
                if (this.find("input[type=hidden]").prop("required")) {
                    this.closest(".field").toggleClass("error", true);
                    return false;
                }
            }
            return true;
        }.bind(this))
    }
});