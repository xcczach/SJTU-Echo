import { createRouter, createWebHistory } from 'vue-router';
import Home from '../components/HomeApp.vue';
import Chat from '../components/ChatApp.vue';

const routes = [
  {
    path: '/',
    redirect: '/chat',
  },
  {
    path: '/home',
    name: 'Home',
    component: Home,
  },
  {
    path: '/chat',
    name: 'Chat',
    component: Chat,
  },
  {
    path: '/chat/:sessionID',
    name: 'ChatSession',
    component: Chat,
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
