const targetHost = "https://a6ce-123-121-180-211.ngrok-free.app";
const port = "9834";
const apiUrl = targetHost.includes("localhost") ? `${targetHost}:${port}/rag` : `${targetHost}/rag`;
export { apiUrl };