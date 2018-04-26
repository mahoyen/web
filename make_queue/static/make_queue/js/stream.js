$('.stream.image').each(function () {
    var chatSocket = new WebSocket(
        'wss://' + window.location.host +
        '/ws/stream/' + $(this).attr("name") + '/');

    chatSocket.image = $(this);

    chatSocket.onmessage = function (e) {
        var data = JSON.parse(e.data);
        var image = new Image();
        image.src = 'data:image/jpeg;base64,' + data['image'];
        chatSocket.image.html('');
        chatSocket.image.append(image);
    };

    chatSocket.onclose = function (e) {
        console.error('Socket closed unexpectedly');
    };
});

$('.stream.image').click(function () {
    $(this).toggleClass('fullscreen');
    $('#fader').toggleClass('fullscreen');
    $('#closefullscreen').toggleClass('fullscreen');
});

$('#closefullscreen').click(function () {
    $('.fullscreen').each(function () {
        $(this).removeClass('fullscreen');
    });
});
