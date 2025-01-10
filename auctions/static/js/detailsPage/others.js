//=====================tinymce=====================
tinymce.init({
    selector: '#desc',
    menubar: false,
    toolbar: false,
    plugins: 'code',
    readonly: true,
    statusbar: false,
    content_style: `body { padding: 0; margin: 0; height: auto; }`,
    setup: function (editor) {
        editor.on('init', function () {
            editor.getContainer().style.border = 'none';
        });
    }
});

//=====================tinymce=====================

function toggleTitle(element) {
    const titleSpan = element.querySelector('span');
    titleSpan.classList.toggle('line-clamp-1');
}
