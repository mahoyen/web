$('#user').parent().dropdown({
    onChange: function (username, text) {
        $.ajax(langPrefix + "/reservation/quota/user/" + username + "/", {
            success: function (data, textStatus) {
                $("#user-quotas").html(data);
                setupDeleteModal();
            }
        })
    }
});

$("#hide_used_quotas").checkbox({
    onChange: function () {
        $(".quota_card").filter(function () {
            return parseInt($(this).data("reservations-left")) <= 0;
        }).toggleClass("make_hidden", $(this).is(":checked"))
    }
});