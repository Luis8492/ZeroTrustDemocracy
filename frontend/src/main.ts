import { mount } from 'svelte';
import App from './App.svelte';
import './themes/themes.css';

const target = document.getElementById('app');
if (!target) {
  throw new Error('Mount target #app not found');
}

mount(App, { target });
