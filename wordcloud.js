// Draws the home page picture: a word cloud of the words used across this site.
// The words and counts come from build.py (in the #cloud-words script tag); the layout is
// a seeded spiral, so the cloud comes out the same every time.
(function () {
  var holder = document.querySelector('.wordcloud');
  var data = document.getElementById('cloud-words');
  if (!holder || !data) return;

  var W = 480, H = 280, CELL = 2;
  var COLORS = ['#c8f08f', '#9ff2e9', '#f6f39a', '#ffffff', '#f7b6e0', '#c9b8ff', '#8fd24e', '#55d3f0', '#ffd27f'];
  var FONT = '"Coming Soon", cursive';
  var words = JSON.parse(data.textContent);

  function rng(seed) { // mulberry32
    return function () {
      seed |= 0; seed = seed + 0x6D2B79F5 | 0;
      var t = Math.imul(seed ^ seed >>> 15, 1 | seed);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }

  function draw() {
    var dpr = Math.min(window.devicePixelRatio || 1, 3);
    var canvas = document.createElement('canvas');
    canvas.width = W * dpr; canvas.height = H * dpr;
    canvas.setAttribute('role', 'img');
    canvas.setAttribute('aria-label', 'A word cloud of the words on this site: ' + words.slice(0, 8).map(function (w) { return w[0]; }).join(', '));
    var ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);

    var GW = W / CELL, GH = H / CELL;
    var taken = new Uint8Array(GW * GH);
    var rand = rng(2015);
    var max = words[0][1], min = words[words.length - 1][1];

    words.forEach(function (entry, i) {
      var word = entry[0], k = max === min ? 1 : (entry[1] - min) / (max - min);
      var size = Math.round(13 + 43 * Math.sqrt(k));
      var upright = i > 2 && rand() < 0.22;
      var color = COLORS[Math.floor(rand() * COLORS.length)];

      // Draw the word on its own small canvas, then read which grid cells it covers.
      var m = (function () { var c = document.createElement('canvas').getContext('2d'); c.font = size + 'px ' + FONT; return c.measureText(word); })();
      var tw = Math.ceil(m.actualBoundingBoxLeft + m.actualBoundingBoxRight) + 2;
      var th = Math.ceil(m.actualBoundingBoxAscent + m.actualBoundingBoxDescent) + 2;
      var w = upright ? th : tw, h = upright ? tw : th;
      var sprite = document.createElement('canvas');
      sprite.width = Math.ceil(w * dpr); sprite.height = Math.ceil(h * dpr);
      var s = sprite.getContext('2d');
      s.scale(dpr, dpr);
      if (upright) { s.translate(0, h); s.rotate(-Math.PI / 2); }
      s.font = size + 'px ' + FONT;
      s.fillStyle = color;
      s.fillText(word, m.actualBoundingBoxLeft + 1, m.actualBoundingBoxAscent + 1);

      var cw = Math.ceil(w / CELL) + 2, ch = Math.ceil(h / CELL) + 2; // one spare cell of padding all round
      var mask = new Uint8Array(cw * ch);
      var px = s.getImageData(0, 0, sprite.width, sprite.height).data, step = CELL * dpr;
      for (var y = 0; y < sprite.height; y++) {
        for (var x = 0; x < sprite.width; x++) {
          if (px[(y * sprite.width + x) * 4 + 3] < 40) continue;
          var gx = Math.floor(x / step) + 1, gy = Math.floor(y / step) + 1;
          for (var dy = -1; dy <= 1; dy++) for (var dx = -1; dx <= 1; dx++) mask[(gy + dy) * cw + gx + dx] = 1;
        }
      }
      var cells = [];
      for (var j = 0; j < mask.length; j++) if (mask[j]) cells.push([j % cw, Math.floor(j / cw)]);

      // Walk out from the middle on an oval spiral until the word fits.
      var start = rand() * Math.PI * 2;
      for (var t = 0; t < 900; t += 0.12) {
        var ox = Math.round((GW - cw) / 2 + 1.75 * t * Math.cos(t + start) * 0.5);
        var oy = Math.round((GH - ch) / 2 + t * Math.sin(t + start) * 0.5);
        if (ox < 0 || oy < 0 || ox + cw > GW || oy + ch > GH) { if (t > 200) break; continue; }
        var clash = false;
        for (var c = 0; c < cells.length; c++) {
          if (taken[(oy + cells[c][1]) * GW + ox + cells[c][0]]) { clash = true; break; }
        }
        if (clash) continue;
        for (c = 0; c < cells.length; c++) taken[(oy + cells[c][1]) * GW + ox + cells[c][0]] = 1;
        ctx.drawImage(sprite, (ox + 1) * CELL, (oy + 1) * CELL, w, h);
        break;
      }
    });
    holder.appendChild(canvas);
  }

  var ready = document.fonts && document.fonts.load ? document.fonts.load('40px "Coming Soon"') : Promise.resolve();
  ready.then(draw, draw);
})();
