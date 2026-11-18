// static server for the film + frame sink
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, 'film');
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2', '.png': 'image/png', '.svg': 'image/svg+xml' };
function start(onFrame) {
  return new Promise((res) => {
    const srv = http.createServer((req, rsp) => {
      const u = new URL(req.url, 'http://x');
      if (req.method === 'POST' && u.pathname === '/frame') {
        const chunks = [];
        req.on('data', (c) => chunks.push(c));
        req.on('end', async () => { await onFrame(+u.searchParams.get('w'), +u.searchParams.get('i'), Buffer.concat(chunks)); rsp.writeHead(200); rsp.end('ok'); });
        return;
      }
      const f = path.join(ROOT, u.pathname === '/' ? 'index.html' : u.pathname);
      if (!f.startsWith(ROOT) || !fs.existsSync(f)) { rsp.writeHead(404); rsp.end(); return; }
      rsp.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
      fs.createReadStream(f).pipe(rsp);
    });
    srv.listen(0, '127.0.0.1', () => res({ srv, port: srv.address().port }));
  });
}
module.exports = { start };
