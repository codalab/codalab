var Competition;
(function (Competition) {

    Competition.invokePhaseButtonOnOpen = function (id) {
        var btn = $("#" + id + " .button.selected")[0];
        if (btn === undefined) {
            btn = $("#" + id + " .button.active")[0];
            if (btn === undefined) {
                btn = $("#" + id + " .button")[0];
            }
        }
        btn.click();
    }

    function decorateLeaderboardButton(btn, submitted) {
        if (submitted) {
            btn.removeClass("leaderBoardSubmit");
            btn.addClass("leaderBoardRemove");
            btn.text("Remove from Leaderboard");
        } else {
            btn.removeClass("leaderBoardRemove");
            btn.addClass("leaderBoardSubmit");
            btn.text("Submit to Leaderboard");
        }
    }

    function updateLeaderboard(competition, submission, cstoken, btn) {
        var url = "/api/competition/" + competition + "/submission/" + submission + "/leaderboard";
        var op = 'delete';
        if (btn.hasClass("leaderBoardSubmit")) {
            op = 'post';
        }
        request = $.ajax({
            url: url,
            type: op,
            datatype: 'text',
            data: {
                'csrfmiddlewaretoken': cstoken,
            },
            success: function (response, textStatus, jqXHR) {
                var added = op == 'post';
                if (added) {
                    var rows = $('#user_results td.status');
                    rows.removeClass('submitted');
                    rows.addClass('not_submitted');
                    rows.html("");
                    var row = $('#' + submission + ' td.status');
                    row.addClass('submitted');
                    row.html('<i class="enclosed-foundicon-checkmark"></i>');
                    $('#user_results button.leaderBoardRemove').each(function (index) {
                        decorateLeaderboardButton($(this), false);
                    });
                } else {
                    var row = $('#' + submission + ' td.status');
                    row.removeClass('submitted');
                    row.addClass('not_submitted');
                    row.html("");
                }
                decorateLeaderboardButton(btn, added);
            },
            error: function (jsXHR, textStatus, errorThrown) {
                alert("An error occurred. Please try again or report the issue");
            },
            beforeSend: function (xhr) {
                xhr.setRequestHeader("X-CSRFToken", cstoken);
            }
        });
    };

    Competition.getPhaseSubmissions = function (competitionId, phaseId, cstoken) {
        $(".competition_submissions").html("").append("<div class='competitionPreloader'></div>").children().css({ 'top': '200px', 'display': 'block' });
        var url = "/competitions/" + competitionId + "/submissions/" + phaseId;
        $.ajax({
            type: "GET",
            url: url,
            cache: false,
            success: function (data) {
                $(".competition_submissions").html("").append(data);
                $('#fileUploadButton').on('click', function () {
                    var disabled = $('#fileUploadButton').hasClass('disabled');
                    if (!disabled) {
                        $('#details').html("");
                        $('#fileUpload').click();
                    }
                });
                $('#fileUpload').liteUploader(
                {
                    script: '/api/competition/' + competitionId + '/submission',
                    allowedFileTypes: 'application/zip,application/x-zip-compressed',
                    maxSizeInBytes: 104857600,
                    csrfmiddlewaretoken: cstoken,
                    customParams: {
                        'csrfmiddlewaretoken': cstoken
                    },
                    before: function () {
                        $('#fileUploadButton').addClass('disabled');
                        $('#fileUploadButton').text("Submitting...");
                        return true;
                    },
                    each: function (file, errors) {
                        if (errors.length > 0) {
                            $('#details').html('The selected file is not a valid ZIP file under 100MB.');
                        }
                    },
                    success: function (response) {
                        $("#user_results tr.noData").remove();
                        $("#user_results").append(Competition.displayNewSubmission(response));
                        $('#user_results #' + response.id + ' .enclosed-foundicon-plus').on("click", function () { Competition.showOrHideSubmissionDetails(this) });
                        $('#fileUploadButton').removeClass("disabled");
                        $('#fileUploadButton').text("Submit Results");
                        $('#user_results #' + response.id + ' .enclosed-foundicon-plus').click();
                    },
                    fail: function (jqXHR) {
                        var msg = "An unexpected error occured.";
                        if (jqXHR.status == 403) {
                            msg = jqXHR.responseJSON.detail;
                        }
                        $('#details').html(msg);
                        $('#fileUploadButton').text("Submit Results");
                        $('#fileUploadButton').removeClass('disabled');
                    }
                });

                $('#user_results .enclosed-foundicon-plus').on('click', function () {
                    Competition.showOrHideSubmissionDetails(this);
                });
            },
            error: function (xhr, status, err) {
                $(".competition_submissions").html("<div class='alert-error'>An error occurred. Please try refreshing the page.</div>");
            }
        });
    }

    Competition.getPhaseResults = function (competitionId, phaseId) {
        $(".competition_results").html("").append("<div class='competitionPreloader'></div>").children().css({ 'top': '200px', 'display': 'block' });
        var url = "/competitions/" + competitionId + "/results/" + phaseId;
        $.ajax({
            type: "GET",
            url: url,
            cache: false,
            success: function (data) {
                $(".competition_results").html("").append(data);
                $(".column-selectable").click(function (e) {
                    var table = $(this).closest("table");
                    $(table).find(".column-selected").removeClass();
                    $(this).addClass("column-selected");
                    columnId = $(this).attr("name");
                    var rows = table.find('td').filter(function () {
                        return $(this).attr("name") === columnId;
                    }).addClass("column-selected");
                    var sortedRows = rows.slice().sort(function (a, b) {
                        var ar = parseInt($.text([$(a).find("span")]));
                        if (isNaN(ar)) { ar = 100000; }
                        var br = parseInt($.text([$(b).find("span")]));
                        if (isNaN(br)) { br = 100000; }
                        return ar - br;
                    });
                    var parent = rows[0].parentNode.parentNode;
                    var clonedRows = sortedRows.map(function () { return this.parentNode.cloneNode(true); });
                    for (var i = 0; i < clonedRows.length; i++) {
                        $(clonedRows[i]).find("td.row-position").text($(clonedRows[i]).find("td.column-selected span").text());
                        parent.insertBefore(clonedRows[i], rows[i].parentNode);
                        parent.removeChild(rows[i].parentNode);
                    }
                });
            },
            error: function (xhr, status, err) {
                $(".competition_results").html("<div class='alert-error'>An error occurred. Please try refreshing the page.</div>");
            }
        });
    }

    Competition.registationCanProceed = function () {
        if ($("#checkbox").is(":checked") === true) {
            $("#participateButton").removeClass("disabledStatus");
        } else {
            $("#participateButton").addClass("disabledStatus");
        };
    };

    Competition.displayRegistrationStatus = function () {
        var sOut = "";
        sOut = "<div class='participateInfoBlock pendingApproval'>"
        sOut += "<div class='infoStatusBar'></div>"
        sOut += "<div class='labelArea'>"
        sOut += "<label class='regApprovLabel'>Your request to participate in this challenge has been received and a decision is pending.</label>"
        sOut += "<label></label>"
        sOut += "</div>"
        sOut += "</div>"
        return sOut;
    }

    function fmt2(val) {
        var s = val.toString();
        if (s.length == 1) {
            s = "0" + s;
        }
        return s;
    }
    function lastModifiedLabel(dtString) {
        var d;
        if ($.browser.msie && (parseInt($.browser.version) === 8)) {
            d = new Date();
            var dd = parseInt(dtString.substring(8, 10), 10);
            var mm = parseInt(dtString.substring(5, 7), 10);
            var yr = parseInt(dtString.substring(0, 4), 10);
            var hh = parseInt(dtString.substring(11, 13), 10);
            var mn = parseInt(dtString.substring(14, 16), 10);
            var sc = parseInt(dtString.substring(17, 19), 10);
            d.setUTCDate(dd);
            d.setUTCMonth(mm);
            d.setUTCFullYear(yr);
            d.setUTCHours(hh);
            d.setUTCMinutes(mn);
            d.setUTCSeconds(sc);
        } else {
            d = new Date(dtString);
        }
        var dstr = $.datepicker.formatDate('M dd, yy', d).toString();
        var hstr = d.getHours().toString();
        var mstr = fmt2(d.getMinutes());
        var sstr = fmt2(d.getSeconds());
        return "Last modified: " + dstr + " at " + hstr + ":" + mstr + ":" + sstr;
    }

    Competition.displayNewSubmission = function (response) {
        var elemTr = $("#submission_details_template #submission_row_template tr").clone();
        $(elemTr).attr("id", response.id.toString());
        $(elemTr).addClass(Competition.oddOrEven(response.submission_number));
        $(elemTr).children().each(function (index) {
            switch (index) {
                case 0: if (response.status === "finished") { $(this).val("1"); } break;
                case 1: $(this).html(response.submission_number.toString()); break;
                case 2:
                    var fmt = function (val) {
                        var s = val.toString();
                        if (s.length == 1) {
                            s = "0" + s;
                        }
                        return s;
                    }
                    var dt = new Date(response.submitted_at);
                    var d = $.datepicker.formatDate('mm/dd/yy', dt).toString();
                    var h = dt.getHours().toString();
                    var m = fmt(dt.getMinutes());
                    var s = fmt(dt.getSeconds());
                    $(this).html(d + " " + h + ":" + m + ":" + s);
                    break;
                case 3: $(this).html(Competition.getSubmissionStatus(response.status)); break;
            }
        }
      );
        return elemTr;
    }

    Competition.oddOrEven = function (x) {
        return (x & 1) ? "odd" : "even";
    }

    Competition.getSubmissionStatus = function (status) {
        var subStatus = "Unknown";
        if (status === "submitting") {
            subStatus = "Submitting";
        } else if (status === "submitted") {
            subStatus = "Submitted";
        } else if (status === "running") {
            subStatus = "Running";
        } else if (status === "failed") {
            subStatus = "Failed";
        } else if (status === "cancelled") {
            subStatus = "Cancelled";
        } else if (status === "finished") {
            subStatus = "Finished";
        }
        return subStatus;
    }

    Competition.showOrHideSubmissionDetails = function (obj) {
        var nTr = $(obj).parents('tr')[0];
        if ($(obj).hasClass("enclosed-foundicon-minus")) {
            $(obj).removeClass("enclosed-foundicon-minus");
            $(obj).addClass("enclosed-foundicon-plus");
            $(nTr).next("tr.trDetails").remove();
        }
        else {
            $(obj).removeClass("enclosed-foundicon-plus");
            $(obj).addClass("enclosed-foundicon-minus");
            var elem = $("#submission_details_template .trDetails").clone();
            elem.find("a").each(function (i) { $(this).attr("href", $(this).attr("href").replace("_", nTr.id)) });
            var phasestate = $('#phasestate').val();
            var state = $(nTr).find("input[name='state']").val();
            if ((phasestate == 1) && (state == 1)) {
                var btn = elem.find("button");
                btn.removeClass("hide");
                var submitted = $(nTr).find(".status").hasClass("submitted");
                var competition = $("#competitionId").val();
                decorateLeaderboardButton(btn, submitted);
                btn.on('click', function () {
                    updateLeaderboard(competition, nTr.id, $("#cstoken").val(), btn);
                });
            }
            else {
                var status = $(nTr).find(".statusName").html();
                var btn = elem.find("button").addClass("hide");
                if ($.trim(status) === "Submitting" || $.trim(status) === "Submitted" || $.trim(status) === "Running") {
                    btn.removeClass("hide");
                    btn.text("Refresh status")
                    btn.on('click', function () {
                        Competition.updateSubmissionStatus($("#competitionId").val(), nTr.id, this)
                    });
                }
            }
            $(nTr).after(elem);
        }
    }

    Competition.updateSubmissionStatus = function (competitionId, submissionId, obj) {
        $(obj).parents(".submission_details").find(".preloader-handler").append("<div class='competitionPreloader'></div>").children().css({ 'top': '25px', 'display': 'block' });
        var url = "/api/competition/" + competitionId + "/submission/" + submissionId;
        $.ajax({
            type: "GET",
            url: url,
            cache: false,
            success: function (data) {
                $('#user_results #' + submissionId).find(".statusName").html(Competition.getSubmissionStatus(data.status));
                if (data.status === "finished") {
                    $('#user_results #' + submissionId + "input:hidden").val("1");
                    var phasestate = $('#phasestate').val();
                    if (phasestate == 1) {
                        $(obj).addClass("leaderBoardSubmit");
                        $(obj).text("Submit to Leaderboard");
                        $(obj).on('click', function () {
                            updateLeaderboard(competitionId, submissionId, $("#cstoken").val(), $(obj));
                        });
                    } else {
                        $(obj).addClass("hide");
                    }
                }
                else if (data.status === 'failed' || data.status === 'cancelled') {
                    $(obj).addClass("hide");
                }
                $(".competitionPreloader").hide();
            },
            error: function (xhr, status, err) {

            }
        });
    }

})(Competition || (Competition = {}));
var prTable;
$(document).ready(function () {

    $("#checkbox").click(function (e) { Competition.registationCanProceed(); });

    $("#participate_form").submit(function (event) {
        event.preventDefault();
        if ($("#participateButton").hasClass("disabledStatus")) {
            return false;
        }
        $("#result").html('');
        var values = $(this).serialize();
        var competitionId = $("#competitionId").val();
        request = $.ajax({
            url: "/api/competition/" + competitionId + "/participate/",
            type: "post",
            dataType: "text",
            data: values,
            success: function (response, textStatus, jqXHR) {
                $('.content form').replaceWith(Competition.displayRegistrationStatus());
            },
            error: function (jsXHR, textStatus, errorThrown) {
                alert("There was a problem registering for this competition.");;
            }
        });
        return false;
    });

    $("#submissions_phase_buttons .button").each(function (e, index) {
        $(this).click(function () {
            var phaseId = $.trim($(this).attr("id").replace("submissions_phase_", ""));
            $("#submissions_phase_buttons .button").removeClass('selected');
            $(this).addClass('selected');
            var competitionId = $("#competitionId").val();
            var cstoken = $("#cstoken").val();
            Competition.getPhaseSubmissions(competitionId, phaseId, cstoken);
        });
    });

    $('a[href="#participate-submit_results"]').click(function (obj) {
        Competition.invokePhaseButtonOnOpen("submissions_phase_buttons");
    });

    $("#results_phase_buttons .button").each(function (e, index) {
        $(this).click(function () {
            var phaseId = $.trim($(this).attr("id").replace("results_phase_", ""));
            $("#results_phase_buttons .button").removeClass('selected');
            $(this).addClass('selected');
            var competitionId = $("#competitionId").val();
            Competition.getPhaseResults(competitionId, phaseId);
        });
    });

    $('#Results').click(function (obj) {
        Competition.invokePhaseButtonOnOpen("results_phase_buttons");
    });

    // This helps make sections appear with Foundation
    $(this).foundation('section', 'reflow');

    $(".top-bar-section ul > li").removeClass("active");
    $("#liCompetitions").addClass("active");

    $(".my_managing .competition-tile #competition-actions").each(function (e, index) {

        $(this).children('#competition-publish-button').click(function () {
            var competition_actions = $(this).parent()[0];
            request = $.ajax({
                url: $(this)[0].value,
                success: function (response, textStatus, jqXHR) {
                    console.log("Published competition.");
                    $(competition_actions).children("#competition-publish-button").hide();
                    $(competition_actions).children("#competition-delete-button").hide();
                    $(competition_actions).children("#competition-unpublish-button").show();
                },
                error: function (jsXHR, textStatus, errorThrown) {
                    console.log("Error publishing competition!");
                }
            });
        });

        $(this).children('#competition-unpublish-button').click(function () {
            // This shows how unpublishing a competition works. We have this commented out
            // because we don't want competition owners to inadvertantly unpublish, then delete
            // competitions that have submissions and results.
            // If this decision is changed in the future simply uncommenting this code will enable
            // competitions to be unpublished.
            // Only unpublished competitions are able to be deleted.
            //var competition_actions = $(this).parent()[0];
            //request = $.ajax({
            //    url: $(this)[0].value,
            //    success: function (response, textStatus, jqXHR) {
            //        console.log("Unpublished competition.");
            //        $(competition_actions).children("#competition-publish-button").show();
            //        $(competition_actions).children("#competition-delete-button").show();
            //        $(competition_actions).children("#competition-unpublish-button").hide()
            //    },
            //    error: function (jsXHR, textStatus, errorThrown) {
            //        console.log("Error unpublishing competition!");
            //    }
            //});
        });

        if ($(this)[0].getAttribute("published") == "True") {
            $(this).children('#competition-delete-button').hide();
            $(this).children('#competition-publish-button').hide();
            $(this).children('#competition-unpublish-button').show();
        } else {
            $(this).children('#competition-delete-button').show();
            $(this).children('#competition-publish-button').show();
            $(this).children('#competition-unpublish-button').hide();
        }
    });

    var loc = window.location.href;
    if (loc !== undefined) {
        if (loc.match(/#participate-submit_results$/i) !== null) {
            Competition.invokePhaseButtonOnOpen("submissions_phase_buttons");
        } else if (loc.match(/#results$/i) !== null) {
            Competition.invokePhaseButtonOnOpen("results_phase_buttons");
        }
    }
});
