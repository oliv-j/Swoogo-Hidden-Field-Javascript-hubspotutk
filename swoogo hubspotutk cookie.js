<script>
  document.addEventListener('DOMContentLoaded', function () {
    try {
      var hiddenField = document.getElementById('registrant-c_5542264'); // change the value to the hidden form field used to store the HubSpot user token
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
        if (cookieValue) {
          try { cookieValue = decodeURIComponent(cookieValue); } catch (e) {}

          // Allow either 32-char hex or GUID with hyphens
          var utkPattern = /^([0-9a-f]{32}|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})$/i;

          if (utkPattern.test(cookieValue)) {
            hiddenField.value = cookieValue;
          }
        }
      }
    } catch (error) {
      // Fail safely without interrupting the page.
    }
  });
</script>
