$(document).ready(function() {
    // Add custom parser for our dates. This can be used by adding 'class="sorter-dates"' to <th>.
    // See 'deprecated_dataset_report.html' for example use.
    $.tablesorter.addParser({
        id: 'dates',
        is: function(s, table, cell, $cell) {
            return false;
        },
        format: function(s, table, cell, cellIndex) {
            const dateString = dateFormatter(s);
            return convertDateStringToNumericValue(dateString);
        },
        type: 'numeric'
    });

    // Attach the tablesorter plugin to tables.
    $("#report-table").tablesorter({});

    $(".js-auto-submit").change(function () {
        $(this).closest("form").submit();
    });
});

/**
 * Convert the final dates, when they have been formatted into a proper format, into a 
 * numerical value. Numerical values are faster and easier to sort in the table.
 * 
 * @param {String} originalDateString The date in string format.
 * @return {Integer} Date converted to a numerical value.
 */
function convertDateStringToNumericValue(originalDateString) {
    const newDate = new Date(originalDateString);
    return newDate.getTime();
}

/**
 * The Finnish date format is a little odd in comparison to the others. This
 * function attemps to convert the Finnish date format into 'mm/dd/yyyy'.
 * 
 * @param {String} originalDateString The date in string format.
 * @return {String} returns date string in a format which can be passed into the Date() class.
 */
function formatFinnishDate(originalDateString) {
    const monthDict = {
        tammikuu: "1",
        helmikuu: "2",
        maaliskuu: "3",
        huhtikuu: "4",
        toukokuu: "5",
        kesäkuu: "6",
        heinäkuu: "7",
        elokuu: "8",
        syyskuu: "9",
        lokakuu: "10",
        marraskuu: "11",
        joulukuu: "12",
    };

    // Turn '24. joulukuu, 2020' into ['24', '12', '2020']
    let reFormattedDate = originalDateString.toLowerCase()
        .replace(/ /g, "")
        .replace(/,/g, ".")
        .split(".");
  
    // Now we should have ['24', '12', '2020']    
    reFormattedDate[1] = monthDict[reFormattedDate[1]];

    // Turn ['24', '12', '2020'] into '12/24/2020'
    return reFormattedDate[1] + "/" + reFormattedDate[0] + "/" + reFormattedDate[2];
}

/**
 * The Date() class doesn't understand Swedish. We need to translate some
 * of the months into English to make the format correct. Some months are the same
 * in English and Swedish.
 * 
 * @param {String} originalDateString The date in string format.
 * @return {String} returns date string in a format which can be passed into the Date() class.
 */
function formatSweEngDate(originalDateString) {
    return originalDateString
        .toLowerCase()
        .replace(/januari/,"January")
        .replace(/februari/,"February")
        .replace(/mars/,"March")
        .replace(/maj/,"May")
        .replace(/juni/,"June")
        .replace(/juli/,"July")
        .replace(/augusti/,"August")
        .replace(/oktober/,"October");
}

/**
 * Wrapper for the formatter functions. This function also makes sure that we don't pass
 * faulty strings into the formatter functions.
 * 
 * @param {String} originalDateString The date in string format.
 * @return {String} returns date string in a format which can be passed into the Date() class.
 */
function dateFormatter(originalDateString) {
    if (checkFinnishDateFormat(originalDateString)) {
        return formatFinnishDate(originalDateString);
    }

    if (checkSweEngDateFormat(originalDateString)) {
        return formatSweEngDate(originalDateString);
    }

    return ''
}

/**
 * Check if a string matches the finnish date pattern used in the reports.
 * Example: '24. joulukuu, 2020'
 * 
 * @param {String} dateString The date in string format according to the example above.
 * @return {Boolean}
 */
function checkFinnishDateFormat(dateString) {
    const reFin = new RegExp(/^\d{1,2}. [a-zA-ZåäöÅÄÖ]+, \d{4}$/);
    return reFin.test(dateString);
}

/**
 * Check if a string matches the finnish date pattern used in the reports.
 * Example: 'April 12, 2002'
 * Note: this date is valid input for Date().
 * 
 * @param {String} dateString The date in string format according to the example above.
 * @return {Boolean}
 */
function checkSweEngDateFormat(dateString) {
    const reEngSwe = new RegExp(/^[a-zA-ZåäöÅÄÖ]+ \d{1,2}, \d{4}$/);
    return reEngSwe.test(dateString);
}
