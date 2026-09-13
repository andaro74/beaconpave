// L4 smoke: load the served static player and write k6's end-of-test summary.
//
// This decides nothing. surfaces/web-player/emit.py maps the summary into the verdict
// envelope. Responses received and requests that never reached the surface (status 0)
// are counted apart. A run in which no request received a response reads as INFRA: the
// surface was never there. Any other run is decided by its thresholds, and dropped
// connections already count toward http_req_failed. Measured before this was written:
// a served 404 closes each connection, and 905 requests of one 10 s run never connected
// while the rest received 404, so "any transport error is INFRA" misread a surface
// answering wrongly as a harness that was never there.
//
// usage: k6 run -e TARGET=<url> -e SUMMARY_OUT=<summary.json> loadtest/smoke.js
//
// Owning seat: AI Quality (the thresholds); Platform Engineering (the profile).
import http from 'k6/http';
import { check } from 'k6';
import { Counter } from 'k6/metrics';

const transportErrors = new Counter('transport_errors');
const responsesReceived = new Counter('responses_received');

export const options = {
  vus: 5,
  duration: '10s',
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<200'],
  },
};

export default function () {
  const res = http.get(__ENV.TARGET);
  if (res.status === 0) {
    transportErrors.add(1);
  } else {
    responsesReceived.add(1);
  }
  check(res, { 'status is 200': (r) => r.status === 200 });
}

export function handleSummary(data) {
  return { [__ENV.SUMMARY_OUT]: JSON.stringify(data, null, 2) };
}
