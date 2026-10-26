// Fragment support for the thesis pages: an "On this page" list of sections
// under the current chapter in the sidebar, highlighting of the linked item,
// and a re-scroll once MathJax has changed the layout.

(function () {
  "use strict";

  function target() {
    var id = decodeURIComponent(location.hash.slice(1));
    return id ? document.getElementById(id) : null;
  }

  // Anchors are empty <a id> elements; highlight the block they belong to.
  // For an equation that is the display math right after its anchor.
  function blockOf(el) {
    if (/^eq-/.test(el.id)) {
      var p = el.closest("p");
      var next = p && p.nextElementSibling;
      while (next && !next.querySelector("mjx-container, .math.display")) next = next.nextElementSibling;
      if (next) return next;
    }
    var block = el.closest("h1, h2, h3, h4, p, div.Theorem, div.Def, li");
    if (block && block.tagName === "P" && block.textContent.trim() === "") {
      // a figure/table anchor paragraph: highlight the figure and its caption
      return block.nextElementSibling || block;
    }
    return block || el;
  }

  var flashed = null;
  window.thesisGoToHash = function () {
    var el = target();
    if (!el) return;
    el.scrollIntoView();
    var block = blockOf(el);
    if (flashed) flashed.classList.remove("targeted");
    block.classList.add("targeted");
    flashed = block;
  };

  function buildToc() {
    var current = document.querySelector(".sidebar li.current");
    if (!current) return;
    var headings = document.querySelectorAll("main h2, main h3");
    if (!headings.length) return;
    var list = document.createElement("ol");
    list.className = "toc";
    headings.forEach(function (h) {
      var link = h.querySelector("a.heading-link");
      if (!link) return;
      var li = document.createElement("li");
      li.className = "toc-" + h.tagName.toLowerCase();
      var a = document.createElement("a");
      a.href = link.getAttribute("href");
      // Copy the rendered heading (math included), minus anchors and the "#".
      h.childNodes.forEach(function (node) {
        if (node.nodeType === 1 && node.matches("a.heading-link, a[id]:empty")) return;
        a.appendChild(node.cloneNode(true));
      });
      li.appendChild(a);
      list.appendChild(li);
    });
    current.appendChild(list);
  }

  // Once MathJax has typeset the page: build the section list (it copies the
  // rendered headings) and jump to the #fragment again, since typesetting
  // changes the page height.  Without MathJax, do it on load.
  var ready = false;
  function onTypeset() {
    if (ready) return;
    ready = true;
    buildToc();
    window.thesisGoToHash();
  }
  document.addEventListener("DOMContentLoaded", function () {
    window.thesisGoToHash();
    var startup = window.MathJax && window.MathJax.startup;
    if (startup && startup.promise) {
      startup.promise.then(onTypeset, onTypeset);
    } else {
      window.addEventListener("load", onTypeset);
    }
  });
  window.addEventListener("hashchange", window.thesisGoToHash);
  // Close the mobile drawer after picking a section.
  document.addEventListener("click", function (e) {
    if (e.target.closest(".sidebar a")) {
      var toggle = document.getElementById("nav-toggle");
      if (toggle) toggle.checked = false;
    }
  });
})();
