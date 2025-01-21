//=====================tinymce=====================
tinymce.init({
    selector: '#desc',
    menubar: false,
    toolbar: false,
    plugins: 'autoresize',
    readonly: true,
    statusbar: false,
    setup: function (editor) {
        editor.on('init', function () {
            const editorContainer = editor.getContainer();
            editorContainer.style.border = 'none';
            editorContainer.style.outline = 'none';
        });
    },
});


//=====================tinymce=====================

function toggleTitle(element) {
    const titleSpan = element.querySelector('span');
    titleSpan.classList.toggle('line-clamp-1');
}
