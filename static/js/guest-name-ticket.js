$(document).ready(function(){
    $(document).on("blur",".input-data",function(){
        let value=$(this).val();
        let td=$(this).parent("td");
        let type=td.data("type");
        sendToServer(td.data("id"),value,type);
    });

    $(document).on("keypress",".input-data",function(e){
        let key=e.which;
        if(key===13){
            let value=$(this).val();
            let td=$(this).parent("td");
            let type=td.data("type");
            sendToServer(td.data("id"),value,type);
        }
    });

    function sendToServer(id,value,type){
        let endpoint = document.getElementById('endpoint-url-div').getAttribute('url');
        $.ajax({
            // url:"http://127.0.0.1:8000/order/ticket/save/",
            url: endpoint,
            type:"POST",
            data:{id:id,type:type,value:value},
        })
        .done(function(response){
            console.log(response);
        })
        .fail(function(){
           console.log("Error Occured");
        });

    }

});
