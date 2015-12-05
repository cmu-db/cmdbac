$('.collapse').on('show.bs.collapse', function(event) {
	icon = $('#' + $(this).attr('id') + '-icon');
	icon.removeClass("glyphicon-plus").addClass("glyphicon-minus");
	event.stopPropagation();
}).on('hidden.bs.collapse', function(event) {
	icon = $('#' + $(this).attr('id') + '-icon');
	icon.removeClass("glyphicon-minus").addClass("glyphicon-plus");
	event.stopPropagation();
});