$(document).ready(function(){
    $(document).on("blur",".input-data",function(){
        let value=$(this).val();
        let td=$(this).parent("td");
        let type=td.data("type");
        saveGuestName(td.data("id"),value,type);
    });

    $(function() {
        $('.tooltip-wrapper').tooltip({position: "bottom"});
    });

    $(document).on("keypress",".input-data",function(e){
        let key=e.which;
        if(key===13){
            let value=$(this).val();
            let td=$(this).parent("td");
            let type=td.data("type");
            saveGuestName(td.data("id"),value,type);
        }
    });

    function saveGuestName(id, value, type){
        $.ajax({
            url: "/order/ticket/save/",
            type:"POST",
            data:{id:id, type:type, value:value},
        })
        .fail(function(){
           console.log("Error Occured");
        });

    }

});
