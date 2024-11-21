<script setup>
import HelloWorld from './Hello.vue'
import TheWelcome from './TheWelcome.vue'
</script>

<template>
    <div class="general">
        <header>
            <!-- <img alt="Vue logo" class="logo" src="./assets/logo.svg" width="125" height="125" /> -->
            <div class="wrapper">
                <HelloWorld msg="Welcome to SJTU Echo" />
            </div>
        </header>
        <main>
            <!-- <TheWelcome /> -->
        </main>
    </div>
</template>

<style scoped>
.general {
    display: flex;
    flex-direction: row;
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

