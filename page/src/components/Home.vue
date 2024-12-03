<script setup>
import HelloWorld from './Hello.vue'
import TheWelcome from './TheWelcome.vue'
import WelcomeItem from './WelcomeItem.vue'
</script>

<template>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&display=swap" rel="stylesheet">
    <div class="general">
      <main>
          <img src="../assets/home.png" alt="echo" width="500vw" margin="50px">
      </main>
      <header>
        <div class="wrapper">
            <HelloWorld/>
        </div>
      </header>

    </div>
</template>

<style scoped>
.general {
    display: flex;
    flex-direction: row;
    justify-content: center;
    align-items: center;
    color: var(--background-primary);
}

header {
  line-height: 1.5;
}

@media (min-width: 1024px) {
  header {
    display: flex;
    place-items: center;
    /* padding-right: calc(var(--section-gap) / 2); */
  }

  header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
    width: 50vw;
  }

  main {
    margin-left: -100px;
    margin-right: 50px;
  }
}
</style>

