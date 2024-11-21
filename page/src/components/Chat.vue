<template>
    <div class="chat-app">
      <div class="sidebar">
        <div class="sidebar-top">
          <button class="sidebar-create-button" @click="promptNewSession">New Session</button>
        </div>

        <div class="sidebar-sessions">
          <div v-for="(session, index) in sessions"
          :key="session.id" class="sidebar-session-card">
            {{ session.name }}
            <button class="siderbar-session-card-options-button" @click="toggleMenu(index)">...</button>
            <div
              v-if="activeMenuIndex === index"
              class="sidebar-dropdown-menu"
            >
              <button @click="renameSession(index)">Rename</button>
              <button @click="deleteSession(index)">Delete</button>
            </div>
          </div>
        </div>
      </div>

      <div class="window">
        <h2 class="window-title">Chat with SJTU Echo</h2>
        <div class="window-start">
          <p class="window-start-line1">Welcome to SJTU Echo! Click on a session to start chatting.</p>
          <p class="window-start-line2">You can create a new session by clicking the "New Session" button.</p>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from "vue";

  // store all sessions
  const sessions = ref([]);
  const activeMenuIndex = ref(null);

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
  }

  onMounted(() => {
    loadSessionData(); // Ensure the DOM is ready
  });
  </script>
  
  <style scoped>
  .chat-app { /* Overall layout */
    display: flex;
    flex-direction: row;
    justify-content: flex-start;
    height: 100vh;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  }
  
  .sidebar {
    width: 20vw;
    height: 100vh;
    background-color: #202020;
    color: white;
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
    color: white;
    top: 0;
    left: 0;
    display: flex;
    flex-direction: column;
  }
  
  .window-title {
    margin: 0;
    font-size: 1.5rem;
    color: var(--accent-color);
    font-weight: 700;
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
    width: 140px;
    height: 45px;
    transition: background-color 0.3s;
    text-align: center;
    background-color: var(--primary-color);
    color: white;
    border: none;
    border-radius: 10px;
    cursor: pointer;
    font-size: 1rem;
    font-weight: 700;
    margin: 10px 20px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  }

  .sidebar-create-button:hover {
    background-color: var(--accent-color);
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
    border-bottom: 1px solid var(--primary-color);
    display: flex;
    justify-content: space-between;
    position: relative;
    align-items: center;
    cursor: pointer;
    color: white;
    transition: background-color 0.3s;
  }

  .sidebar-session-card:hover {
    background-color: var(--primary-color);
  }

  .siderbar-session-card-options-button {
    background: none;
    border: none;
    border-radius: 5px;
    color: white;
    font-size: 1.2rem;
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
    background-color: rgba(0, 0, 0, 0.8);
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
    text-align: left;
    padding: 10px 15px;
    width: 100%;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    transition: background-color 0.3s;
    font-weight: 600;
  }

  .sidebar-dropdown-menu button:hover {
    background-color: rgba(255, 255, 255, 0.1);
  }
  
  /* 消息窗口样式 */
  .chat-window {
    flex: 1;
    padding: 20px;
    background-color: #f5f5f5;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  
  .message {
    max-width: 70%;
    padding: 10px;
    border-radius: 10px;
    word-wrap: break-word;
  }
  
  .message.user {
    align-self: flex-end;
    background-color: #daf1da;
  }
  
  .message.bot {
    align-self: flex-start;
    background-color: #e0e0e0;
  }
  
  /* 底部输入栏样式 */
  .input-bar {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 20px;
    background-color: white;
    border-top: 1px solid #ddd;
  }
  
  .input-text {
    flex: 1;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 5px;
    resize: none;
    font-size: 1rem;
  }
  
  .send-button {
    padding: 10px 20px;
    background-color: #4caf50;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 1rem;
  }
  
  .send-button:hover {
    background-color: #45a049;
  }
  </style>
  