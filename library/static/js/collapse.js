$('.collapse').on('show.bs.collapse', function(){
   $(this).siblings().find(".glyphicon-plus").removeClass("glyphicon-plus").addClass("glyphicon-minus");
}).on('hidden.bs.collapse', function(){
   $(this).siblings().find(".glyphicon-minus").removeClass("glyphicon-minus").addClass("glyphicon-plus");
});