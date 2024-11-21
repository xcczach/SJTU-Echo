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
    <h1 class="purple">{{ msg }}</h1>
    <h3>
      Your AI assistant for campus guide and information.
    </h3>

    <div class="home-btn-container">
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
  justify-content: center;
}

.home-btn-start {
  display: block;
  margin: 40px auto;
  padding: 20px 40px;
  font-size: 1.2rem;
  color: var(--text-primary);
  /* background-color: #4CAF50; */
  background-color: transparent;
  border: 2px solid var(--primary-color);
  border-radius: 10px;
  cursor: pointer;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-weight: 700;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.home-btn-start:hover {
  background-color: var(--primary-color);
}
</style>
