const http = require('http');
const { getDefaultConfig } = require('expo/metro-config');

const BACKEND = { host: '127.0.0.1', port: 5000 };
const PREFIX = '/api';

const config = getDefaultConfig(__dirname);

// Development only: forward /api/* to the local backend, so a phone that can load the app
// (LAN or Expo tunnel) can reach the API through the same address.
config.server = {
  ...config.server,
  enhanceMiddleware: (middleware) => (req, res, next) => {
    if (!req.url.startsWith(`${PREFIX}/`)) return middleware(req, res, next);
    const upstream = http.request(
      {
        ...BACKEND,
        method: req.method,
        path: req.url.slice(PREFIX.length),
        headers: { ...req.headers, host: `${BACKEND.host}:${BACKEND.port}` },
      },
      (reply) => {
        res.writeHead(reply.statusCode ?? 502, reply.headers);
        reply.pipe(res);
      },
    );
    upstream.on('error', () => {
      res.writeHead(502, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: { message: 'The backend is not running.', code: 'bad_gateway' } }));
    });
    req.pipe(upstream);
  },
};

module.exports = config;
