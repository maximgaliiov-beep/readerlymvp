// Local dev config template.
//
// For local development:
//   cp config.example.js config.local.js   # then fill in real keys
//
// At container build/run time, entrypoint.sh generates config.js from
// Cloud Run env vars — config.js is never committed and never copied
// into the image at build time.
//
// index.html includes config.js (in prod) or config.local.js (in dev,
// rename it to config.js for the script tag to find it).

window.READERLY_CONFIG = {
  AZURE_KEY: 'PASTE_AZURE_SPEECH_KEY_HERE',
  AZURE_REGION: 'eastus',
  GEMINI_API_KEY: 'PASTE_GEMINI_API_KEY_HERE',
  GEMINI_MODEL: 'gemini-2.5-flash'
};
