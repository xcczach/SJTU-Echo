<script setup>
import HelloWorld from './Hello.vue'
import TheWelcome from './TheWelcome.vue'
import WelcomeItem from './WelcomeItem.vue'
</script>

<template>
    <div class="general">
      <header>
        <div class="wrapper">
            <HelloWorld msg="Welcome to SJTU Echo" />
        </div>
      </header>
      <main>
      </main>
    </div>
</template>

<style scoped>
.general {
    display: flex;
    flex-direction: row;
    justify-content: center;
    align-items: center;
}

header {
  line-height: 1.5;
}

@media (min-width: 1024px) {
  header {
    display: flex;
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }
}
</style>

