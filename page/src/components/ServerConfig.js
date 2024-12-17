// const targetHost = "reptile-flying-obviously.ngrok-free.app";
const targetHost = "localhost";
const port = "9834";
const apiUrl = targetHost.includes("localhost") ? `http://${targetHost}:${port}` : targetHost;
const ragEndpoint = `${apiUrl}/rag`;
const asrEndpoint = `${apiUrl}/asr`;
const ttsEndpoint = `${apiUrl}/tts`;
export { ragEndpoint, asrEndpoint, ttsEndpoint };