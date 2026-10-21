<script lang="ts">
  import { onMount } from 'svelte';
  import { session, setStudent } from './lib/session.svelte';
  import { router } from './lib/router.svelte';
  import { api, ApiError } from './lib/api';
  import BottomNav from './components/BottomNav.svelte';
  import Register from './views/Register.svelte';
  import Home from './views/Home.svelte';
  import TopicView from './views/Topic.svelte';
  import Quiz from './views/Quiz.svelte';
  import Leaderboard from './views/Leaderboard.svelte';
  import Profile from './views/Profile.svelte';

  // Validate the stored session once per app start (e.g. student deleted by teacher).
  onMount(async () => {
    const s = session.student;
    if (!s) return;
    try {
      const fresh = await api.getStudent(s.id);
      setStudent(fresh);
    } catch (e) {
      if (e instanceof ApiError && e.code === 'unknown_student') setStudent(null);
      // network errors: keep the stored session
    }
  });
</script>

{#if !session.student}
  <Register />
{:else}
  {#key router.route}
    {#if router.route.name === 'home'}
      <Home />
    {:else if router.route.name === 'topic'}
      <TopicView topicId={router.route.topicId} />
    {:else if router.route.name === 'quiz'}
      <Quiz topicId={router.route.topicId} difficulty={router.route.difficulty} />
    {:else if router.route.name === 'leaderboard'}
      <Leaderboard />
    {:else if router.route.name === 'profile'}
      <Profile />
    {/if}
  {/key}
  {#if router.route.name !== 'quiz'}
    <BottomNav />
  {/if}
{/if}
