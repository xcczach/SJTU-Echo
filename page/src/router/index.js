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
    meta: {
      title: 'SJTU Echo Home',
    }
  },
  {
    path: '/chat',
    name: 'Chat',
    component: Chat,
    meta: {
      title: 'SJTU Echo',
    }
  },
  {
    path: '/chat/:sessionID',
    name: 'ChatSession',
    component: Chat,
    meta: {
      title: 'SJTU Echo Chat',
    }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, _from, next) => {
  if (to.meta.title) {
    document.title = to.meta.title;
  }
  next();
});

export default router;
