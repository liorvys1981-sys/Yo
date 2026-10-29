/* YO Clone landing i18n — ES default / EN toggle. Sin dependencias. */
(function () {
  "use strict";
  var I18N = { en: {
    n1:"Process", n2:"Privacy", n3:"Capabilities", n4:"Real status",
    h1:"A digital clone of you, inside YO, under your consent",
    lead:"YO Clone guides the creation of your digital representation: captures with quality evaluation, consent per data type, and a live conversation answered by EL_YO's real pipeline — no prefabricated responses.",
    disc:"STATUS: PARTIAL. Photorealistic generation, voice and lip-sync are BLOCKED by external providers (no keys in this environment). This page shows no generated replica and does not simulate a video call.",
    s1:"How it is created",
    p1:'<strong>Explicit consent</strong> per data type (photos, voice, video), revocable at any time.',
    p2:"<strong>Guided capture</strong>: 5–10 photos recommended; the system scores lighting and contrast of each shot and asks for more if fidelity misses the threshold.",
    p3:"<strong>Deterministic quality evaluation</strong>; cancel, retry or delete always available.",
    p4:"<strong>Representation registry</strong>: the clone is your representation — never a new sovereign identity; all its captures are provenance-tracked.",
    p5:"<strong>Provider transfers</strong> only with an independent cryptographic authorization (R1). Without it, nothing leaves the system.",
    s2:"Privacy and control",
    v1:'<strong>Your data is yours:</strong> complete deletion available anytime, with ledger evidence.',
    v2:'<strong>Per-user isolation:</strong> one user\'s captures never mix with another\'s.',
    v3:'<strong>Nothing is sent without authorization:</strong> any provider transfer requires consent plus R1 authorization (verified channel phrase).',
    v4:'<strong>The clone is not identity:</strong> it is a representation with structural <code>is_identity=False</code>; it replaces neither your identity nor ELLA\'s.',
    s3:"Capabilities",
    c1t:"Consent-first onboarding", c1p:"Prior explanation, scopes per data type, cancel/retry/delete. Tested: 25 tests.",
    c2t:"Capture and quality", c2p:"Deterministic lighting/contrast scoring, progress with fidelity threshold, requests for additional captures.",
    c3t:"Live conversation", c3p:"Turns, interruptions, visible states, per-phase measured latency. Responses come from EL_YO's real pipeline; TTS and animation report their (blocked) status honestly.",
    c4t:"Governance", c4p:"Changes to the clone and data transfers go through Evolution and R1 Authorization; append-only evidence.",
    s4:"Real status and limits",
    st1:"<strong>Implemented and tested:</strong> onboarding, consent, capture with quality evaluation, clone representation registry, live conversation with measured latency. Suite: 25/25.",
    st2:"<strong>Blocked by external providers (EXTERNAL_BLOCKED):</strong> photorealistic avatar generation, text-to-speech, lip-sync and model providers. Interfaces and gates are implemented and tested; the real replica is NOT simulated.",
    st3:"<strong>Not verified:</strong> real browser rendering, video call with visual replica. The complete system is not declared finished.",
    d1:"Test suite (25 tests)", d2:"FASE 1 audit", d3:"External dependencies",
    ft:"YO Clone — part of EL_YO. No trackers, no CDNs. Sealed facts, honest limits."
  }};
  var btn = document.getElementById("lang-toggle");
  var nodes = document.querySelectorAll("[data-i18n]");
  var cur = "es";
  function apply(lang){ cur = lang;
    nodes.forEach(function(n){ var k = n.getAttribute("data-i18n");
      if (lang==="en" && I18N.en[k]!==undefined) n.innerHTML = I18N.en[k];
      else if (n.hasAttribute("data-es")) n.innerHTML = n.getAttribute("data-es"); });
    document.documentElement.setAttribute("lang", lang);
    btn.textContent = lang==="es" ? "EN" : "ES"; }
  nodes.forEach(function(n){ n.setAttribute("data-es", n.innerHTML); });
  btn.addEventListener("click", function(){ apply(cur==="es" ? "en" : "es"); });
})();
