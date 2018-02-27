(function ($) {
  'use strict';

  /* forms */
  tinymce.init({
    selector: '.rich-editor:enabled',
    width: 784,
    plugins : 'autolink link',
    menubar: '',
    toolbar: 'undo redo | bold italic underline strikethrough | link | removeformat',
    statusbar: false,
  });

  setTimeout(function(){
    $('.form-feedback').fadeOut(1000);
  }, 3000);


  /* court list */
  $('#closed-court-toggle').change(function(){
    $('tr.closed-court').toggleClass('hidden');
  })

  //add case insensitive contains
  jQuery.expr[":"].icontains = jQuery.expr.createPseudo(function (arg) {
    return function (elem) {
      return jQuery(elem).text().toUpperCase().indexOf(arg.toUpperCase()) >= 0;
    };
  });

  $('#court-search-box').on('input',function(e){
    var search = $(this).val();
    $('#closed-court-toggle').prop('checked', true).prop('disabled', search);
    $('#court-list tr:not(:first-child)').addClass('hidden');
    $("#court-list td:first-child:icontains('" + search + "')").parent().removeClass('hidden');
  })

  /* reordering js */
  $("#sortable").sortable({
    axis: "y"
  });
  $("#sortable").disableSelection();
  $("#sortable").on("sortstop", function(event, ui) {
    var sortedIDs = $("#sortable").sortable("toArray");
    var ordering = JSON.stringify(sortedIDs);
    $("#new_sort_order").val(ordering);
  });
})(jQuery);
