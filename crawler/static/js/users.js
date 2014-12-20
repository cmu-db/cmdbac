var req;
function sendRequest() {
    if(window.XMLHttpRequest) {
        req = new XMLHttpRequest();
    } else {
        req = new ActiveXObject("Microsoft.XMLHTTP");
    }
    req.onreadystatechange = handleResponse;
    var offset = document.getElementById("user-list").getElementsByTagName("li").length;
  
    req.open("GET", "/blog/get-users/" + offset.toString(), true);
    req.send();
}

function handleResponse() {
    if(req.readyState != 4 || req.status != 200) {
        return;
    }
    var list = document.getElementById("user-list");
    var xmlData = req.responseXML;
    var items = xmlData.getElementsByTagName("item");
    for(var i = 0; i < items.length; i++) {
        var id = items[i].getElementsByTagName("id")[0].textContent;
        var first_name = items[i].getElementsByTagName("first_name")[0].textContent;
        var last_name = items[i].getElementsByTagName("last_name")[0].textContent;
        var newItem = document.createElement("li");
        newItem.innerHTML = "<a href=\"/blog/follow-user/" + id + "\">" + first_name + " " + last_name + "</a>";
        list.appendChild(newItem);
    }
}
window.setInterval(sendRequest, 1000);
