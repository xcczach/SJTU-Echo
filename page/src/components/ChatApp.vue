<template>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link
    href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap"
    rel="stylesheet">
  <div class="chat-app">
    <div class="sidebar">
      <div class="sidebar-top">
        <button class="sidebar-create-button" @click="promptNewSession">
          New Session
        </button>
      </div>

      <div class="sidebar-sessions">
        <div v-for="(session, index) in sessions" :key="session.id" class="sidebar-session-card">
          {{ session.name }}
          <button class="siderbar-session-card-enter-button" @click="navigateToSession(session.id)">
            <el-icon>
              <EnterOutlined />
            </el-icon>
          </button>
          <button class="siderbar-session-card-options-button" @click="toggleMenu(index)">
            <el-icon>
              <MoreFilled />
            </el-icon>
          </button>
          <div v-if="activeMenuIndex === index" class="sidebar-dropdown-menu">
            <button @click="renameSession(index)">Rename</button>
            <button @click="deleteSession(index)">Delete</button>
          </div>
        </div>
      </div>
    </div>

    <div class="window">
      <div class="window-nav">
        Chat with SJTU Echo
        <button class="window-nav-home" @click="navigateHome(null)">
          <el-icon>
            <HomeFilled />
          </el-icon>
        </button>
      </div>
      <div class="window-start" v-if="sessionID === null">
        <p class="window-start-line1">Welcome to SJTU Echo! Click on a session to start chatting.</p>
        <p class="window-start-line2">You can create a new session by clicking the "New Session" button.</p>
      </div>
      <div class="window-chat" v-if="sessionID !== null">
        <div v-for="(message, index) in MessagesforSession()" :key="index" class="window-chat-card"
          :class="message.from">
          <div v-html="message.content"></div>
          <div v-if="message.audioUrl">
            <audio style="display: none;" :id="'audio-' + index" @ended="audioEnded(index)">
              <source :src="message.audioUrl" type="audio/mp3" />
              Your browser does not support the audio element.
            </audio>
            <button @click="playAudio(index)" class="inline-play-button">
              <el-icon v-if="!isPlaying[index]">
                <VideoPlay />
              </el-icon>
              <el-icon v-else>
                <VideoPause />
              </el-icon>
              <!-- {{ isPlaying[index] ? "Pause" : "Play" }} -->
            </button>
          </div>
        </div>

      </div>
      <div class="window-enter" v-if="sessionID !== null">
        <button @click="isRecording ? stopRecording() : startRecording()" class="window-enter-voice"
          :class="{ 'recording': isRecording, 'not-recording': !isRecording }">
          <el-icon>
            <Microphone />
          </el-icon>
        </button>
        <textarea class="window-enter-textbox" v-model="userPrompt" placeholder="Enter your prompt here...">
          </textarea>
        <button class="window-enter-send" @click="textfieldSendPrompt()" :disabled="!userPrompt">
          <el-icon>
            <Promotion />
          </el-icon>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from "vue";
import { useRoute } from 'vue-router';
import axios from "axios";
import MarkdownIt from "markdown-it";
import { Microphone, VideoPlay, VideoPause } from "@element-plus/icons-vue";
import { ragEndpoint, asrEndpoint, ttsEndpoint } from "./ServerConfig.js";
const md = new MarkdownIt({
  html: false,
  linkify: true,
  typographer: true,
});

const sessions = ref([]);   // store all sessions
const messages = ref([]);   // store all messages
const activeMenuIndex = ref(null);
const sessionID = useRoute().params.sessionID ?? null;
const userPrompt = ref("");

const isRecording = ref(false);
let mediaRecorder = null;
let audioChunks = [];

const isPlaying = ref([]);

const sendAudioToASR = async (sampleRate, audioData, audioUrl) => {
  try {
    const response = await fetch(asrEndpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        sample_rate: sampleRate,
        audio_data: audioData,
      }),
    });

    if (!response.ok) {
      throw new Error(`ASR request failed: ${response.statusText}`);
    }

    const result = await response.text();
    sendPrompt(result, audioUrl);
  } catch (error) {
    console.error("Error sending audio to ASR:", error);
  }
};

function audioEnded(index) {
  isPlaying.value[index] = false;
}

function playAudio(index) {
  const audioElement = document.getElementById(`audio-${index}`);

  if (audioElement.paused) {
    audioElement.play();
    isPlaying.value[index] = true;
  } else {
    audioElement.pause();
    isPlaying.value[index] = false;
  }
}

const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.onstart = () => {
      isRecording.value = true;
      audioChunks = []; // Clear audio data
    };

    mediaRecorder.ondataavailable = (event) => {
      audioChunks.push(event.data);
    };

    mediaRecorder.onstop = async () => {
      isRecording.value = false;
      const audioBlob = new Blob(audioChunks, { type: "audio/mp3" });
      const arrayBuffer = await audioBlob.arrayBuffer();
      const audioContext = new AudioContext();
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
      const audioData = Array.from(audioBuffer.getChannelData(0));
      const sampleRate = audioBuffer.sampleRate;
      const audioUrl = URL.createObjectURL(audioBlob);
      sendAudioToASR(sampleRate, audioData, audioUrl);
    };

    mediaRecorder.start();
  } catch (error) {
    console.error("Error accessing microphone:", error);
  }
};

const stopRecording = () => {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
  }
}

function navigateHome() {
  window.location.href = "/home";
}

function navigateToSession(sessionID) {
  // Redirect to the chat window with the session ID
  window.location.href = `/chat/${sessionID}`;
}

function toggleMenu(index) {
  if (activeMenuIndex.value === index) {
    activeMenuIndex.value = null;
  } else {
    activeMenuIndex.value = index;
  }
}

function renameSession(index) {
  const sessionName = sessions.value[index].name;
  const newSessionName = prompt("Enter a new session name:", sessionName);
  if (newSessionName && newSessionName !== sessionName) {
    if (isSessionExists(newSessionName)) {
      alert(`Session "${newSessionName}" already exists!`);
    } else {
      sessions.value[index].name = newSessionName;
      saveSessionData();
      alert(`Session "${sessionName}" renamed to "${newSessionName}"!`);
    }
  }
  activeMenuIndex.value = null;
}

function deleteSession(index) {
  const sessionName = sessions.value[index].name;
  if (confirm(`Are you sure you want to delete the session "${sessionName}"?`)) {
    activeMenuIndex.value = null;
    sessions.value.splice(index, 1);
    saveSessionData();
    alert(`Session "${sessionName}" deleted!`);
  }
}

function generateSessionID() {
  return Array(20)
    .fill(0)
    .map(() => Math.random().toString(36).charAt(2))
    .join('');
}

function isSessionExists(sessionName) {
  return sessions.value.some((session) => session.name === sessionName);
}

function promptNewSession() {
  // Give a prompt to the user to enter a new session name
  const sessionName = prompt("Enter a session name:");
  if (sessionName) {
    if (isSessionExists(sessionName)) {
      alert(`Session "${sessionName}" already exists!`);
    } else {
      const sessionID = generateSessionID();
      const newSessionObj = {
        name: sessionName,
        id: sessionID,
        messages: [],
      };
      sessions.value.push(newSessionObj);
      saveSessionData();
      alert(`Session "${sessionName}" created!`);
    }
  }
}

function scrollToBottom() {
  const chatWindow = document.querySelector(".window-chat");
  setTimeout(() => {
    chatWindow.scrollTop = chatWindow.scrollHeight;
  }, 0);
}

async function getTTSResult(content) {
  const response = await axios.post(ttsEndpoint, {
    sessionID: sessionID,
    text: content,
  }, {
    responseType: "blob",
  });
  const audioBlob = response.data;
  const audioUrl = URL.createObjectURL(audioBlob);
  return audioUrl;
}

async function playLatestAudio(newMessage) {
  await nextTick();
  const currentSessionMessages = MessagesforSession();
  const index = currentSessionMessages.length - 1;
  if (newMessage.audioUrl) {
    const audioElement = document.getElementById(`audio-${index}`);
    if (audioElement) {
      audioElement.play();
      isPlaying.value[index] = true;
    }
  }
}

async function sendPrompt(message, audioUrl) {
  if (message) {
    messages.value.push({ from: "user", content: message, sessionID: sessionID, audioUrl: audioUrl === undefined ? null : audioUrl });
    userPrompt.value = "";
    saveMessageData();
    scrollToBottom();

    try {
      const response = await axios.post(ragEndpoint, {
        sessionID: sessionID,
        messages: [{
          type: "human",
          content: message,
          response_metadata: {}
        }],
      });
      if (response.status === 200) {
        const response_body = response.data.messages[response.data.messages.length - 1].content;
        const audioUrl = await getTTSResult(response_body);
        const response_link = response.data.messages[response.data.messages.length - 1].response_metadata.link;
        const response_content =
          response_body +
          (response_link
            ? `\n\n[相关链接](${response_link})`
            : "");

        let parsedContent = md.render(response_content);
        parsedContent = parsedContent.replace(
          /<a\s+href=/g,
          '<a target="_blank" href='
        );
        const newMessage = { from: "bot", content: parsedContent, sessionID: sessionID, audioUrl: audioUrl };
        messages.value.push(newMessage);
        saveMessageData();
        scrollToBottom();
        await playLatestAudio(newMessage);
      }
    } catch (error) {
      console.error(error);
    }
  }
}

async function textfieldSendPrompt() {
  const message = document.querySelector(".window-enter-textbox").value;
  sendPrompt(message);
  document.querySelector(".window-enter-textbox").value = "";
}

function MessagesforSession() {
  return messages.value.filter((message) => message.sessionID === sessionID);
}

function saveMessageData() {
  const text_messages = messages.value.map((message) => {
    return {
      from: message.from,
      content: message.content,
      sessionID: message.sessionID,
      audioUrl: null,
    };
  });
  localStorage.setItem("messages", JSON.stringify(text_messages));
}

// save the session data to local storage
function saveSessionData() {
  localStorage.setItem("sessions", JSON.stringify(sessions.value));
}

// load the session data from local storage
function loadSessionData() {
  const sessionData = localStorage.getItem("sessions");
  if (sessionData) {
    sessions.value = JSON.parse(sessionData);
  }
  const messageData = localStorage.getItem("messages");
  if (messageData) {
    messages.value = JSON.parse(messageData);
  }
  scrollToBottom();
}

onMounted(() => {
  loadSessionData(); // Ensure the DOM is ready
});
</script>

<style scoped>
.chat-app {
  /* Overall layout */
  display: flex;
  flex-direction: row;
  justify-content: flex-start;
  height: 100vh;
  font-family: var(--font-family);
}

.sidebar {
  width: 20vw;
  height: 100vh;
  background-color: var(--background-secondary);
  color: var(--text-primary);
  position: fixed;
  top: 0;
  left: 0;
  display: flex;
  flex-direction: column;
  padding: 20px 0;
}

.window {
  width: 75vw;
  height: 100vh;
  margin-left: 23vw;
  padding-top: 20px;
  position: fixed;
  background: transparent;
  color: var(--text-primary);
  top: 0;
  left: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.window-nav {
  display: flex;
  flex-direction: row;
  width: 100%;
  margin: 0;
  font-size: 1.5rem;
  color: var(--primary-color);
  font-weight: 700;
}

.window-nav-home {
  position: absolute;
  right: 0;
  background: none;
  border: none;
  color: #AAAAAA;
  width: 40px;
  height: 40px;
  cursor: pointer;
  transition: color 0.3s;
}

.window-nav-home:hover {
  color: var(--neutral-light);
}

.window-start {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 20px;
  padding: 20px;
  height: 100%;
  text-align: center;
  color: rgb(110, 110, 110);
}

.window-start-line1 {
  font-size: 2rem;
  font-weight: 600;
}

.window-start-line2 {
  font-size: 1.2rem;
  font-weight: 400;
}

.sidebar-top {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 20px;
  padding: 20px;
}

.sidebar-create-button {
  width: 150px;
  height: 45px;
  transition: background-color 0.3s;
  text-align: center;
  background-color: var(--secondary-color);
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  margin: 10px 20px;
  padding: 10px;
  font-family: var(--font-family);
  font-size: 1rem;
  font-weight: 700;
}

.sidebar-create-button:hover {
  background-color: var(--secondary-color);
  border: none;
}

.sidebar-sessions {
  display: flex;
  flex-direction: column;
  height: 80vh;
  gap: 10px;
  padding: 20px;
  overflow-y: auto;
}

.sidebar-session-card {
  padding: 10px 10px;
  border-radius: 5px;
  border-bottom: 1px solid var(--secondary-color);
  display: flex;
  justify-content: space-between;
  position: relative;
  align-items: center;
  color: var(--text-secondary);
  font-weight: 500;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.sidebar-session-card:hover {
  background-color: var(--secondary-color);
  color: var(--background-primary);
}

.siderbar-session-card-enter-button {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  width: 85%;
  background-color: transparent;
  z-index: 1;
  border: none;
  cursor: pointer;
}

.siderbar-session-card-options-button {
  background: none;
  border: none;
  width: 30px;
  height: 30px;
  border-radius: 5px;
  color: var(--text-secondary);
  font-size: 0.5rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.siderbar-session-card-options-button:hover {
  background: var(--accent-color);
}

.sidebar-dropdown-menu {
  position: absolute;
  height: auto;
  top: 100%;
  right: 0;
  background-color: var(--text-secondary);
  border: 1px solid var(--neutral-dark);
  border-radius: 5px;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  z-index: 10;
}

.sidebar-dropdown-menu button {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  padding: 10px 15px;
  width: 100%;
  transition: background-color 0.3s;
  font-weight: 600;
  font-family: var(--font-family);
}

.sidebar-dropdown-menu button:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.window-enter {
  position: absolute;
  justify-content: center;
  align-items: center;
  bottom: 5vh;
  left: 50%;
  transform: translateX(-50%);
  width: 80%;
  height: 13vh;
  display: flex;
  flex-direction: row;
  gap: 10px;
  padding: 10px;
  background: transparent;
  color: white;
}

.window-enter-textbox {
  padding: 10px;
  background-color: var(--background-secondary);
  border: none;
  border-radius: 20px;
  width: 60%;
  height: 100%;
  resize: none;
  padding: 15px;
  color: var(--text-primary);
  font-size: 1.2rem;
  font-family: var(--font-family);
}

.window-enter-voice {
  padding: 10px 20px;
  width: 60px;
  height: 60px;
  background-color: var(--primary-color);
  color: white;
  border: none;
  border-radius: 15px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.window-enter-voice.recording {
  background-color: #FF3B30;
}

.window-enter-voice.recording:hover {
  background-color: #FF453A;
}

.window-enter-voice.not-recording {
  background-color: var(--primary-color);
}

.window-enter-voice.not-recording:hover {
  background-color: var(--accent-color);
}

.window-enter-send {
  padding: 10px 20px;
  width: 60px;
  height: 60px;
  background-color: var(--primary-color);
  color: white;
  font-size: 1.2rem;
  border: none;
  border-radius: 15px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.window-enter-send:disabled {
  background-color: var(--neutral-dark);
  cursor: not-allowed;
}

.window-enter-send:disabled:hover {
  background-color: var(--neutral-dark);
  cursor: not-allowed;
}

.window-enter-send:hover {
  background-color: var(--accent-color);
}

.window-enter-textbox:focus {
  outline: none;
}

.window-chat {
  display: flex;
  flex-direction: column;
  gap: 10px;
  top: 10px;
  padding: 20px;
  width: 60vw;
  height: 75vh;
  overflow-y: auto;
  scroll-behavior: smooth;
}

.window-chat::-webkit-scrollbar {
  width: 10px;
}

.window-chat::-webkit-scrollbar-track {
  background: var(--background-secondary);
  border-radius: 10px;
}

.window-chat::-webkit-scrollbar-thumb {
  background-color: var(--accent-color);
  border-radius: 10px;
}

.window-chat-card {
  padding: 10px;
  border-radius: 10px;
  display: inline-block;
  max-width: 70%;
  word-wrap: break-word;
}

.window-chat-card.user {
  background-color: var(--primary-color);
  width: 40%;
  color: white;
  align-self: flex-end;
}

.window-chat-card.bot {
  background-color: var(--background-secondary);
  width: 40%;
  color: var(--text-primary);
  align-self: flex-start;
}

.inline-play-button {
  background: var(--secondary-color);
  width: 30px;
  height: 30px;
  background-color: var(--secondary-color);
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}
</style>