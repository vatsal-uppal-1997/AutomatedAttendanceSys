var persist, persist2;
function remove(element) {
  // GET TD
  var owner = element.parentNode;
  //GET TR
  var ownersParent = owner.parentNode;

  var children = new Array();
  for (i=1,j=0;i<6;i=i+2,j++) {
    children[j] = ownersParent.childNodes[i].textContent;
    children[j] = children[j].trim()
  }
  persist = children;
  // GET TABLE
  var grandParent = ownersParent.parentNode;


  // GET Table from which to remove
  var get_tbl = grandParent;
  while (get_tbl.nodeName != 'TR') {
    get_tbl = get_tbl.parentNode;
  }
  get_tbl = get_tbl.children[0].textContent;

  var POSTDATA = "id="+encodeURIComponent(children[0])+"&name="+encodeURIComponent(children[1])+"&section="+encodeURIComponent(children[2])+"&table="+encodeURIComponent(get_tbl);
  console.log(POSTDATA)
  //AJAX

  ajax = new XMLHttpRequest();
  ajax.open('POST', '/remove');
  ajax.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
  ajax.send(POSTDATA);
  ajax,onreadystatechange = function() {
    if (ajax.readyState === XMLHttpRequest.DONE) {
      if (ajax.status === 200) {
        console.log("req 200 !");
      } else {
        console.log("req err !");
      }
    }
  }
  grandParent.parentNode.removeChild(grandParent);
}

function app(element) {
  var parent = element.parentNode;
  var children = parent.children;
  console.log(parent)
  var data = new Array()
  data[0] = children[0].value;
  data[1] = children[1].value;
  var POSTDATA  = "teacher="+encodeURIComponent(data[0])+"&timeout="+encodeURIComponent(data[1]);
  // ajax
  console.log(POSTDATA)
  ajax = new XMLHttpRequest();
  ajax.open('POST', '/start');
  ajax.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
  ajax.send(POSTDATA);
  id = setInterval(function() {
    ajax = new XMLHttpRequest();
    ajax.open('GET','/start');
    ajax.onload = function() {
      if (ajax.status === 200) {
        res = ajax.responseText;
        if (res == "True") {
          element.disabled = true;
        } else {
          clearInterval(id);
          element.disabled = false;
          window.location.reload();
        }
      }
    }
    ajax.send();
  }, 5000);
}
