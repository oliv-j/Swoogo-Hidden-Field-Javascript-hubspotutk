<script>
  document.addEventListener('DOMContentLoaded', function () {
    try {
      var hiddenField = document.getElementById('registrant-c_5542292'); //change the ID to the form field that you want to place the cookie value
      if (hiddenField) {
        function getCookie(name) {
          var nameEQ = name + "=";
          var cookies = document.cookie.split(';');
          for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.indexOf(nameEQ) === 0) {
              return cookie.substring(nameEQ.length, cookie.length);
            }
          }
          return null;
        }
        var cookieValue = getCookie('hubspotutk');
        if (cookieValue && /^[a-zA-Z0-9]+$/.test(cookieValue)) {
          hiddenField.value = cookieValue;
        }
      }
    } catch (error) {
      // Fail safely without interrupting the page.
    }
  });
</script>