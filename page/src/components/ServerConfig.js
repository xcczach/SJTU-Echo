const targetHost = "https://cf9a-36-140-113-198.ngrok-free.app";
const port = "9834";
const apiUrl = targetHost.includes("localhost") ? `http://${targetHost}:${port}` : targetHost;
const ragEndpoint = `${apiUrl}/rag`;
const asrEndpoint = `${apiUrl}/asr`;
const ttsEndpoint = `${apiUrl}/tts`;
export { ragEndpoint, asrEndpoint, ttsEndpoint };