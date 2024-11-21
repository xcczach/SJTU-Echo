<template>
    <div class="chat-app">
      <!-- 顶部导航栏 -->
      <header class="navbar">
        <h1 class="navbar-title">ChatGPT 示例</h1>
      </header>
  
      <!-- 消息窗口 -->
      <main class="chat-window">
        <div v-for="(message, index) in messages" :key="index" :class="['message', message.sender]">
          <p>{{ message.text }}</p>
        </div>
      </main>
  
      <!-- 底部输入栏 -->
      <footer class="input-bar">
        <textarea
          v-model="userInput"
          placeholder="输入您的消息..."
          rows="1"
          class="input-text"
        ></textarea>
        <button @click="sendMessage" class="send-button">发送</button>
      </footer>
    </div>
  </template>
  
  <script setup>
  import { ref } from "vue";
  
  // 消息列表和用户输入
  const messages = ref([
    { sender: "bot", text: "您好！我是您的AI助手。" },
    { sender: "user", text: "你好！" },
  ]);
  const userInput = ref("");
  
  // 发送消息
  function sendMessage() {
    if (userInput.value.trim() !== "") {
      // 用户消息
      messages.value.push({ sender: "user", text: userInput.value });
      userInput.value = "";
  
      // 模拟 AI 回复
      setTimeout(() => {
        messages.value.push({
          sender: "bot",
          text: "很高兴为您服务！请问有什么需要帮助的？",
        });
      }, 500);
    }
  }
  </script>
  
  <style scoped>
  /* 页面全局样式 */
  .chat-app {
    display: flex;
    flex-direction: column;
    height: 100vh;
    font-family: Arial, sans-serif;
  }
  
  /* 顶部导航栏样式 */
  .navbar {
    background-color: #4caf50;
    color: white;
    padding: 10px 20px;
    text-align: center;
  }
  
  .navbar-title {
    margin: 0;
    font-size: 1.5rem;
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
  