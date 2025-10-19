<script>
/**
 * Robustly copy HubSpot's hubspotutk cookie into hidden form field(s).
 * Consent handling intentionally omitted (per request).
 */
(function () {
  // ---- config: add/adjust selectors if needed ----
  var TARGET_SELECTORS = [
    '#registrant-c_5542264',                         // your known field id
    'input[type="hidden"][name="hubspotutk"]',       // common name fallback
    'input[type="hidden"][data-hs-utk]'              // data attribute fallback
  ];

  // ---- helpers ----
  function getCookie(name) {
    var nameEQ = name + "=";
    var parts = document.cookie ? document.cookie.split(';') : [];
    for (var i = 0; i < parts.length; i++) {
      var c = parts[i].trim();
      if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length);
    }
    return null;
  }

  function normalise(val) {
    if (val == null) return null;
    try { val = decodeURIComponent(val); } catch (e) {} // ignore decode errors
    return (val || '').trim();
  }

  // Accept typical UUID (36 chars with dashes) or hex/dash tokens ~24–64 chars
  function isLikelyHsUtk(val) {
    if (!val) return false;
    var uuidLike = /^[a-f0-9-]{36}$/i.test(val);
    var hexish = /^[a-f0-9-]{24,64}$/i.test(val);
    return uuidLike || hexish;
  }

  function findTargets() {
    // de-duplicate elements across selectors
    var seen = new Set();
    var out = [];
    for (var i = 0; i < TARGET_SELECTORS.length; i++) {
      var nodes = document.querySelectorAll(TARGET_SELECTORS[i]);
      for (var j = 0; j < nodes.length; j++) {
        var el = nodes[j];
        if (!seen.has(el)) {
          seen.add(el);
          out.push(el);
        }
      }
    }
    return out;
  }

  function writeUtkIntoFields(value) {
    var wrote = false;
    var targets = findTargets();
    for (var i = 0; i < targets.length; i++) {
      var el = targets[i];
      if (el && el.value !== value) {
        el.value = value;
        wrote = true;
      }
    }
    return wrote;
  }

  function tryCopyOnce() {
    var raw = getCookie('hubspotutk');
    var val = normalise(raw);
    if (!isLikelyHsUtk(val)) return false;
    return writeUtkIntoFields(val);
  }

  // ---- orchestrate timing & retries ----
  function start() {
    // 1) try immediately (in case cookie & field are ready)
    if (tryCopyOnce()) { stopAll(); return; }

    // 2) interval retries (catch late cookie or late field)
    var attempts = 12;                  // ~6 seconds total
    retryTimer = setInterval(function () {
      if (tryCopyOnce() || --attempts <= 0) stopAll();
    }, 500);

    // 3) watch DOM for injected fields (e.g., late-rendered forms)
    try {
      observer = new MutationObserver(function () {
        // try on every meaningful DOM change, but keep it light
        tryCopyOnce();
      });
      observer.observe(document.documentElement || document.body, {
        childList: true,
        subtree: true
      });
    } catch (e) { /* observer optional */ }
  }

  var retryTimer = null;
  var observer = null;

  function stopAll() {
    if (retryTimer) { clearInterval(retryTimer); retryTimer = null; }
    if (observer)  { observer.disconnect(); observer = null; }
  }

  // run after full load; fallback to DOM ready if already past it
  function onLoaded(fn) {
    if (document.readyState === 'complete') {
      fn();
    } else {
      window.addEventListener('load', fn, { once: true });
    }
  }

  onLoaded(start);
})();
</script>