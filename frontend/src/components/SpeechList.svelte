<script lang="ts">
  import type { Speech } from '../lib/types';

  interface Props {
    speeches: Speech[];
    emptyLabel?: string;
  }

  let { speeches, emptyLabel = '（発言なし）' }: Props = $props();

  function roleClass(mark: string): string {
    if (mark === '◆') return 'questioner';
    if (mark === '◎') return 'answerer';
    return 'chair';
  }

  function avatarText(speech: Speech): string {
    const source = (speech.name || speech.role || speech.mark || '').trim();
    // Grab the first non-space character (single CJK glyph or letter).
    const chars = [...source];
    return chars[0] ?? '?';
  }
</script>

{#if speeches.length === 0}
  <p class="empty">{emptyLabel}</p>
{:else}
  <ul class="speeches">
    {#each speeches as speech, i (i)}
      <li class={'speech ' + roleClass(speech.mark)}>
        <div class="avatar" aria-hidden="true">{avatarText(speech)}</div>
        <div class="bubble">
          <div class="meta">
            <span class="mark" aria-hidden="true">{speech.mark}</span>
            {#if speech.name}<span class="name">{speech.name}</span>{/if}
            {#if speech.role}<span class="role">{speech.role}</span>{/if}
          </div>
          <p class="comment">{speech.comment}</p>
        </div>
      </li>
    {/each}
  </ul>
{/if}

<style>
  .speeches {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  .speech {
    display: grid;
    grid-template-columns: 1fr;
    gap: 0;
  }
  .avatar { display: none; }
  .bubble {
    border-radius: var(--radius);
    border: 1px solid var(--border);
    padding: 0.75rem 1rem;
    background: var(--surface);
  }
  .speech.questioner .bubble { background: var(--questioner-bg); color: var(--questioner-text); }
  .speech.answerer .bubble { background: var(--answerer-bg); color: var(--answerer-text); }
  .speech.chair .bubble { background: var(--chair-bg); color: var(--chair-text); }

  .meta {
    display: flex;
    gap: 0.5rem;
    align-items: baseline;
    font-size: 0.85rem;
    opacity: 0.85;
    margin-bottom: 0.25rem;
    flex-wrap: wrap;
  }
  .name { font-weight: 600; }
  .role { opacity: 0.8; }
  .comment {
    margin: 0;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .empty {
    color: var(--text-muted);
    font-style: italic;
  }

  /* ---------- Chat theme overrides ---------- */
  :global([data-theme='chat']) .speeches {
    gap: 1rem;
    padding: 0.5rem 0;
  }
  :global([data-theme='chat']) .speech {
    grid-template-columns: auto minmax(0, 1fr);
    align-items: end;
    column-gap: 0.6rem;
  }
  :global([data-theme='chat']) .avatar {
    display: grid;
    place-items: center;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: var(--surface-alt);
    color: var(--text);
    font-weight: 700;
    font-size: 1rem;
    border: 1px solid var(--border);
    user-select: none;
  }
  :global([data-theme='chat']) .bubble {
    position: relative;
    border-radius: 18px;
    padding: 0.55rem 0.9rem;
    border: none;
    max-width: 80%;
    box-shadow: 0 1px 1px rgba(0, 0, 0, 0.04);
  }
  :global([data-theme='chat']) .meta {
    font-size: 0.75rem;
    margin-bottom: 0.2rem;
  }
  :global([data-theme='chat']) .meta .mark { display: none; }

  /* questioner: right-aligned, blue */
  :global([data-theme='chat']) .speech.questioner {
    grid-template-columns: minmax(0, 1fr) auto;
  }
  :global([data-theme='chat']) .speech.questioner .avatar {
    order: 2;
    background: var(--questioner-avatar);
    color: var(--questioner-avatar-text);
  }
  :global([data-theme='chat']) .speech.questioner .bubble {
    order: 1;
    justify-self: end;
    background: var(--questioner-bubble);
    color: var(--questioner-bubble-text);
    border-bottom-right-radius: 4px;
  }
  :global([data-theme='chat']) .speech.questioner .bubble::after {
    content: '';
    position: absolute;
    right: -6px;
    bottom: 6px;
    width: 0;
    height: 0;
    border-top: 8px solid transparent;
    border-left: 10px solid var(--questioner-bubble);
  }
  :global([data-theme='chat']) .speech.questioner .meta {
    justify-content: flex-end;
    color: var(--questioner-bubble-text);
    opacity: 0.85;
  }

  /* answerer: left-aligned, neutral */
  :global([data-theme='chat']) .speech.answerer .avatar {
    background: var(--answerer-avatar);
    color: var(--answerer-avatar-text);
  }
  :global([data-theme='chat']) .speech.answerer .bubble {
    background: var(--answerer-bubble);
    color: var(--answerer-bubble-text);
    border-bottom-left-radius: 4px;
  }
  :global([data-theme='chat']) .speech.answerer .bubble::after {
    content: '';
    position: absolute;
    left: -6px;
    bottom: 6px;
    width: 0;
    height: 0;
    border-top: 8px solid transparent;
    border-right: 10px solid var(--answerer-bubble);
  }

  /* chair: centered system message */
  :global([data-theme='chat']) .speech.chair {
    grid-template-columns: 1fr;
    justify-items: center;
  }
  :global([data-theme='chat']) .speech.chair .avatar { display: none; }
  :global([data-theme='chat']) .speech.chair .bubble {
    background: transparent;
    color: var(--text-muted);
    font-style: italic;
    text-align: center;
    box-shadow: none;
    padding: 0.25rem 0.5rem;
    max-width: 90%;
    font-size: 0.9rem;
  }
  :global([data-theme='chat']) .speech.chair .meta { display: none; }

  /* ---------- Scroll (和紙) theme overrides ---------- */
  :global([data-theme='scroll']) .speeches {
    gap: 1.5rem;
    padding: 1.25rem 0.5rem;
    line-height: 2;
    border-top: 3px double var(--border);
    border-bottom: 3px double var(--border);
    position: relative;
  }
  :global([data-theme='scroll']) .speech .avatar { display: none; }
  :global([data-theme='scroll']) .bubble {
    background: transparent;
    border: none;
    padding: 0 0.75rem;
  }
  :global([data-theme='scroll']) .meta {
    font-size: 0.78rem;
    margin: 0 0 0.4rem;
    opacity: 0.85;
    letter-spacing: 0.08em;
    border-bottom: 1px dotted var(--border);
    padding-bottom: 0.2rem;
  }
  :global([data-theme='scroll']) .meta .name {
    font-weight: 700;
  }
  :global([data-theme='scroll']) .comment {
    letter-spacing: 0.02em;
    text-indent: 1em;
  }
  :global([data-theme='scroll']) .speech.questioner .bubble {
    border-right: 4px double var(--accent);
    padding-right: 0.75rem;
    padding-left: 0.75rem;
    color: var(--questioner-text);
    background:
      linear-gradient(90deg, transparent 0, transparent calc(100% - 2.5rem),
        rgba(184, 51, 42, 0.04) 100%);
  }
  :global([data-theme='scroll']) .speech.questioner .meta .mark {
    color: var(--accent);
    font-weight: 700;
  }
  :global([data-theme='scroll']) .speech.answerer .bubble {
    border-left: 4px solid var(--answerer-text);
    padding-left: 0.75rem;
    color: var(--answerer-text);
  }
  :global([data-theme='scroll']) .speech.chair .bubble {
    color: var(--chair-text);
    font-style: italic;
    text-align: center;
  }
  :global([data-theme='scroll']) .speech.chair .bubble::before,
  :global([data-theme='scroll']) .speech.chair .bubble::after {
    content: '─';
    color: var(--border);
    margin: 0 0.5rem;
  }

  /* ---------- HUD / Cyber theme overrides ---------- */
  :global([data-theme='hud']) .speeches {
    gap: 1rem;
  }
  :global([data-theme='hud']) .bubble {
    background: var(--surface);
    border: 1px solid var(--border);
    backdrop-filter: blur(10px) saturate(140%);
    -webkit-backdrop-filter: blur(10px) saturate(140%);
    box-shadow: var(--shadow-card);
    position: relative;
    clip-path: polygon(
      8px 0, 100% 0, 100% calc(100% - 8px),
      calc(100% - 8px) 100%, 0 100%, 0 8px
    );
  }
  :global([data-theme='hud']) .speech {
    grid-template-columns: auto minmax(0, 1fr);
    column-gap: 0.75rem;
    align-items: stretch;
  }
  :global([data-theme='hud']) .avatar {
    display: grid;
    place-items: center;
    width: 44px;
    height: 44px;
    border-radius: 2px;
    background: rgba(0, 240, 255, 0.10);
    color: var(--accent);
    border: 1px solid var(--accent);
    font-family: var(--font-mono);
    font-size: 0.95rem;
    letter-spacing: 0.05em;
    box-shadow: 0 0 12px rgba(0, 240, 255, 0.3),
      inset 0 0 10px rgba(0, 240, 255, 0.15);
  }
  :global([data-theme='hud']) .meta {
    font-family: var(--font-mono);
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--text-muted);
    border-bottom: 1px dashed var(--border);
    padding-bottom: 0.25rem;
  }
  :global([data-theme='hud']) .meta .name {
    color: var(--accent);
    text-shadow: 0 0 6px rgba(0, 240, 255, 0.45);
  }
  :global([data-theme='hud']) .speech.questioner .bubble {
    background: var(--questioner-bg);
    color: var(--questioner-text);
    border-left: 3px solid var(--accent);
    box-shadow: -8px 0 18px rgba(0, 240, 255, 0.18),
      var(--shadow-card);
  }
  :global([data-theme='hud']) .speech.questioner .avatar {
    border-color: var(--accent);
    color: var(--accent);
  }
  :global([data-theme='hud']) .speech.answerer .bubble {
    background: var(--answerer-bg);
    color: var(--answerer-text);
    border-left: 3px solid var(--accent-2);
    box-shadow: -8px 0 18px rgba(255, 43, 214, 0.18),
      var(--shadow-card);
  }
  :global([data-theme='hud']) .speech.answerer .avatar {
    border-color: var(--accent-2);
    color: var(--accent-2);
    background: rgba(255, 43, 214, 0.10);
    box-shadow: 0 0 12px rgba(255, 43, 214, 0.3),
      inset 0 0 10px rgba(255, 43, 214, 0.15);
  }
  :global([data-theme='hud']) .speech.answerer .meta .name {
    color: var(--accent-2);
    text-shadow: 0 0 6px rgba(255, 43, 214, 0.45);
  }
  :global([data-theme='hud']) .speech.chair .bubble {
    color: var(--text-muted);
    font-family: var(--font-mono);
    font-size: 0.85rem;
    border-left: 1px dashed var(--border);
  }
  :global([data-theme='hud']) .comment {
    line-height: 1.7;
  }
</style>
