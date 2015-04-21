
$(function () {
    $("#file-input").on('fileloaded', function (event, file, previewId, index, reader) {
        $("#preview-header").text("Предпросмотр: " + file.name);
        reader.onload = function (e) {
            var contents = e.target.result;
            $("#preview").text(contents);
        };
        reader.readAsText(file);
    });
    function parseData(rawData) {

    }
});