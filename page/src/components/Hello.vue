<script setup>
defineProps({
  msg: {
    type: String,
    required: true,
  },
})

function handleClick() {
  window.location.href = '/chat';
}
</script>

<template>
  <div class="greetings">
    <div class="main-title">{{ msg }}</div>
    <div class="sub-title">
      Your AI assistant for campus guide and information.
    </div>

    <div class="home-btn-container">
      <button class="home-btn-video">
        <el-icon><VideoPlay class="video-icon" /></el-icon>
        Video
      </button>
      <button @click="handleClick" class="home-btn-start">Get Started!</button>
    </div>
  </div>
</template>

<style scoped>
h1 {
  font-weight: 500;
  font-size: 2.6rem;
  position: relative;
  top: -10px;
}

h3 {
  font-size: 1.2rem;
}

.main-title {
  text-decoration: none;
  color: var(--text-primary);
  font-family: var(--font-family);
  font-size: 4.5rem;
  font-weight: 800;
  transition: 0.4s;
  padding: 3px;
}

.sub-title {
  font-family: var(--font-family);
  font-size: 3rem;
  font-weight: 500;
  color: var(--neutral-dark);
  margin: 20px 0;
}

.video-icon {
  width: 40px;
  margin-right: 10px;
  margin-top: 5px;
}

.greetings h1,
.greetings h3 {
  text-align: center;
}

@media (min-width: 1024px) {
  .greetings h1,
  .greetings h3 {
    text-align: left;
  }
}

.home-btn-container {
  display: flex;
  margin: 20px auto;
  justify-content: flex-start;
  margin-top: 40px;
}

.home-btn-video {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-right: 40px;
  padding: 5px 40px;
  font-size: 1.2rem;
  color: var(--background-primary);
  background-color: var(--secondary-color);
  border: 2px solid var(--secondary-color);
  border-radius: 10px;
  cursor: pointer;
  font-family: var(--font-family);
  font-weight: 600;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.home-btn-start {
  display: block;
  padding: 5px 40px;
  font-size: 1.2rem;
  color: var(--text-primary);
  background-color: transparent;
  border: 2px solid var(--primary-color);
  border-radius: 10px;
  cursor: pointer;
  font-family: var(--font-family);
  font-weight: 600;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.home-btn-start:hover {
  background-color:  var(--primary-color);
  color: var(--background-primary);
}
</style>
